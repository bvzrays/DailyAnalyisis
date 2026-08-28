from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from collections.abc import Iterator

import msgspec

from gsuid_core.logger import logger
from gsuid_core.data_store import get_res_path
from gsuid_core.utils.plugins_config.models import (
    GSC,
    GsDivider,
    GsIntConfig,
    GsStrConfig,
    GsBoolConfig,
    GsFloatConfig,
    GsListStrConfig,
    GsRepeatGroupConfig,
)
from gsuid_core.utils.plugins_config.gs_config import StringConfig, all_config_list

from .gscore_runtime import PluginPaths, PluginConfig
from .gscore_runtime.auth import WebUIAuthenticator
from .src.shared.constants import PLUGIN_NAME

PLUGIN_ROOT = Path(__file__).resolve().parent
DATA_DIR = get_res_path() / PLUGIN_NAME
LEGACY_DATA_DIR = get_res_path() / "QQGroupDailyAnalysis"
if not DATA_DIR.exists() and LEGACY_DATA_DIR.exists():
    try:
        LEGACY_DATA_DIR.rename(DATA_DIR)
        logger.info("已将旧版群日常分析数据目录迁移至 %s", DATA_DIR)
    except OSError as exc:
        logger.warning("迁移旧版群日常分析数据目录失败: %s", exc)
DATA_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_PATH = DATA_DIR / "config.json"
GSCORE_CONFIG_PATH = DATA_DIR / "gscore_config.json"
GSCORE_CONFIG_DIR = DATA_DIR / "gscore_configs"
GSCORE_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
PluginPaths.set_data_dir(DATA_DIR)

_GROUP_CONFIG_NAMES = {
    "basic": "群分析·基础设置",
    "webui": "群分析·WebUI安全",
    "qq_official": "群分析·QQ官方",
    "t2i_rendering": "群分析·图片渲染",
    "auto_analysis": "群分析·定时分析",
    "llm": "群分析·LLM设置",
    "analysis_features": "群分析·分析功能",
    "daily_comic": "群分析·每日漫画",
    "incremental": "群分析·增量分析",
    "html": "群分析·HTML设置",
    "qq_group_upload": "群分析·群文件上传",
    "prompts": "群分析·提示词",
    "performance": "群分析·并发限流",
}

_NATIVE_GROUP_MEMBERS = {
    "DailyAnalyisis基础配置": {
        "basic",
        "webui",
        "auto_analysis",
        "analysis_features",
        "incremental",
        "performance",
    },
    "DailyAnalyisis LLM配置": {"llm", "daily_comic"},
    "DailyAnalyisis展示配置": {"qq_official", "t2i_rendering", "html", "qq_group_upload", "prompts"},
}


def _schema_default(item: object) -> object:
    if not isinstance(item, dict):
        return deepcopy(item)
    if "default" in item:
        return deepcopy(item["default"])
    children = item.get("items")
    if item.get("type") == "object" and isinstance(children, dict):
        return {key: _schema_default(value) for key, value in children.items()}
    return {}


def load_schema() -> dict:
    data = json.loads((PLUGIN_ROOT / "_conf_schema.json").read_text(encoding="utf-8-sig"))
    return data if isinstance(data, dict) else {}


def default_config() -> dict:
    return {key: _schema_default(value) for key, value in load_schema().items()}


def _merge_defaults(current: object, defaults: object) -> object:
    if not isinstance(defaults, dict):
        return deepcopy(current) if current is not None else deepcopy(defaults)
    source = current if isinstance(current, dict) else {}
    merged = {key: _merge_defaults(source.get(key), value) for key, value in defaults.items()}
    for key, value in source.items():
        if key not in merged:
            merged[key] = deepcopy(value)
    return merged


def _iter_schema_fields(
    schema: dict,
    prefix: tuple[str, ...] = (),
) -> Iterator[tuple[tuple[str, ...], dict]]:
    for key, value in schema.items():
        if not isinstance(value, dict):
            continue
        path = (*prefix, key)
        children = value.get("items")
        if value.get("type") == "object" and isinstance(children, dict):
            yield from _iter_schema_fields(children, path)
        else:
            yield path, value


def _description(spec: dict) -> str:
    description = str(spec.get("description", "")).strip()
    hint = str(spec.get("hint", "")).strip()
    return "\n".join(part for part in (description, hint) if part)


def _string_details(path: tuple[str, ...], spec: dict) -> dict:
    return {
        "schema_path": ".".join(path),
        "schema_type": str(spec.get("type", "string")),
        "multiline": spec.get("type") == "text",
        "json": spec.get("type") in {"file", "template_list"},
    }


def _template_list_specs(spec: dict) -> dict[str, dict]:
    templates = spec.get("templates")
    if not isinstance(templates, dict):
        return {}
    merged: dict[str, dict] = {}
    for template_key, template in templates.items():
        if not isinstance(template, dict) or not isinstance(template.get("items"), dict):
            continue
        for key, child_spec in template["items"].items():
            if key not in merged and isinstance(child_spec, dict):
                merged[key] = deepcopy(child_spec)
    if "__template_key" not in merged:
        template_keys = [str(key) for key in templates]
        merged = {
            "__template_key": {
                "description": "配置类型",
                "type": "string",
                "options": template_keys,
                "default": template_keys[0] if template_keys else "",
                "hint": "选择此条目对应的供应商协议类型。",
            },
            **merged,
        }
    return merged


def _repeat_group_values(data: list[dict[str, GSC]]) -> list[dict[str, object]]:
    values: list[dict[str, object]] = []
    for row in data:
        item: dict[str, object] = {}
        for key, field in row.items():
            if isinstance(field, GsRepeatGroupConfig):
                item[key] = _repeat_group_values(field.data)
            elif isinstance(field, GsDivider):
                continue
            else:
                item[key] = deepcopy(field.data)
        values.append(item)
    return values


def _repeat_group_rows(
    values: object,
    template: dict[str, GSC],
) -> list[dict[str, GSC]]:
    if isinstance(values, str):
        try:
            values = json.loads(values)
        except json.JSONDecodeError:
            return []
    if not isinstance(values, list):
        return []
    rows: list[dict[str, GSC]] = []
    for raw_row in values:
        if not isinstance(raw_row, dict):
            continue
        row: dict[str, GSC] = {}
        for key, field in template.items():
            cloned = deepcopy(field)
            if key in raw_row and not isinstance(cloned, GsDivider):
                raw_value = raw_row[key]
                if isinstance(cloned, GsRepeatGroupConfig) and isinstance(raw_value, list):
                    cloned.data = _repeat_group_rows(raw_value, cloned.template)
                elif type(raw_value) is type(cloned.data):
                    cloned.data = raw_value
                elif isinstance(cloned, GsFloatConfig) and isinstance(raw_value, int) and not isinstance(raw_value, bool):
                    cloned.data = float(raw_value)
            row[key] = cloned
        rows.append(row)
    return rows


def _make_repeat_group_field(path: tuple[str, ...], spec: dict) -> GsRepeatGroupConfig:
    template_specs = _template_list_specs(spec)
    template = {
        key: _make_gscore_field((*path, key), child_spec)
        for key, child_spec in template_specs.items()
    }
    for key, field in template.items():
        if key == "api_key" and isinstance(field, GsStrConfig):
            field.secret = True
    return GsRepeatGroupConfig(
        title=str(spec.get("description") or path[-1]),
        desc=_description(spec),
        data=[],
        template=template,
    )


def _migrate_template_list_file(path: Path) -> None:
    if not path.exists():
        return
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    if not isinstance(raw, dict):
        return
    changed = False
    schema_by_path = {".".join(field_path): field_spec for field_path, field_spec in _SCHEMA_FIELDS}
    for key, spec in schema_by_path.items():
        if spec.get("type") != "template_list":
            continue
        stored = raw.get(key)
        if not isinstance(stored, dict) or stored.get("type") != "GsStrConfig":
            continue
        field = _make_repeat_group_field(tuple(key.split(".")), spec)
        field.data = _repeat_group_rows(stored.get("data", ""), field.template)
        raw[key] = msgspec.to_builtins(field)
        changed = True
    if changed:
        path.write_text(json.dumps(raw, ensure_ascii=False, indent=4), encoding="utf-8")


def _make_gscore_field(path: tuple[str, ...], spec: dict) -> GSC:
    title = str(spec.get("description") or path[-1])
    description = _description(spec)
    default = deepcopy(spec.get("default"))
    field_type = spec.get("type")
    options = spec.get("options")
    slider_value = spec.get("slider")
    slider = slider_value if isinstance(slider_value, dict) else {}

    if field_type == "bool":
        return GsBoolConfig(
            title=title,
            desc=description,
            data=bool(default),
            secret=bool(spec.get("secret", False)),
        )
    if field_type == "int":
        int_options = [int(value) for value in options] if isinstance(options, list) else []
        maximum = slider.get("max")
        return GsIntConfig(
            title=title,
            desc=description,
            data=int(default or 0),
            max_value=int(maximum) if isinstance(maximum, (int, float)) else None,
            options=int_options,
            secret=bool(spec.get("secret", False)),
        )
    if field_type == "float":
        minimum = slider.get("min")
        maximum = slider.get("max")
        return GsFloatConfig(
            title=title,
            desc=description,
            data=float(default or 0),
            min_value=float(minimum) if isinstance(minimum, (int, float)) else None,
            max_value=float(maximum) if isinstance(maximum, (int, float)) else None,
            secret=bool(spec.get("secret", False)),
        )
    if field_type == "list":
        values = [str(value) for value in default] if isinstance(default, list) else []
        string_options = [str(value) for value in options] if isinstance(options, list) else []
        return GsListStrConfig(
            title=title,
            desc=description,
            data=values,
            options=string_options,
            secret=bool(spec.get("secret", False)),
        )
    if field_type == "template_list":
        return _make_repeat_group_field(path, spec)
    if field_type == "file":
        encoded = json.dumps(default, ensure_ascii=False, indent=2)
        return GsStrConfig(
            title=title,
            desc=f"{description}\n请使用 JSON 格式编辑。".strip(),
            data=encoded,
            details=_string_details(path, spec),
            secret=bool(spec.get("secret", False)),
        )
    string_options = [str(value) for value in options] if isinstance(options, list) else []
    return GsStrConfig(
        title=title,
        desc=description,
        data=str(default or ""),
        options=string_options,
        details=_string_details(path, spec),
        secret=bool(spec.get("secret", False)),
    )


def _build_gscore_group(group_key: str, group: dict) -> dict[str, GSC]:
    group_title = str(group.get("description") or group_key)
    config: dict[str, GSC] = {
        f"__group__.{group_key}": GsDivider(
            title=group_title,
            desc=str(group.get("hint", "")),
            data=group_title,
        )
    }
    for path, spec in _iter_schema_fields({group_key: group}):
        config[".".join(path)] = _make_gscore_field(path, spec)
    return config


def _build_native_group(group_keys: set[str]) -> dict[str, GSC]:
    config: dict[str, GSC] = {}
    for group_key, group in _SCHEMA.items():
        if group_key not in group_keys or not isinstance(group, dict):
            continue
        group_title = str(group.get("description") or group_key)
        config[f"__group__.{group_key}"] = GsDivider(
            title=group_title,
            desc=str(group.get("hint", "")),
            data=group_title,
        )
        for path, spec in _iter_schema_fields({group_key: group}):
            config[".".join(path)] = _make_gscore_field(path, spec)
    return config


_SCHEMA = load_schema()
_DEFAULTS = default_config()
_SCHEMA_FIELDS = tuple(_iter_schema_fields(_SCHEMA))
_TEMPLATE_LIST_PATHS = {
    ".".join(path)
    for path, spec in _SCHEMA_FIELDS
    if spec.get("type") == "template_list"
}
_STRUCTURED_PATHS = {
    ".".join(path)
    for path, spec in _SCHEMA_FIELDS
    if spec.get("type") in {"file", "template_list"}
}
_GROUP_CONFIG_PATHS = {
    group_key: GSCORE_CONFIG_DIR / f"{group_key}.json"
    for group_key, group in _SCHEMA.items()
    if isinstance(group, dict)
}
_NATIVE_CONFIG_PATHS = {
    "DailyAnalyisis基础配置": GSCORE_CONFIG_DIR / "base.json",
    "DailyAnalyisis LLM配置": GSCORE_CONFIG_DIR / "llm.json",
    "DailyAnalyisis展示配置": GSCORE_CONFIG_DIR / "display.json",
}
for _template_config_path in (
    *_GROUP_CONFIG_PATHS.values(),
    *_NATIVE_CONFIG_PATHS.values(),
):
    _migrate_template_list_file(_template_config_path)
_existing_gscore_paths = [
    path
    for path in (
        GSCORE_CONFIG_PATH,
        *_GROUP_CONFIG_PATHS.values(),
        *_NATIVE_CONFIG_PATHS.values(),
    )
    if path.exists()
]
_GSCORE_CONFIG_EXISTED = bool(_existing_gscore_paths)
_GSCORE_CONFIG_MTIME = max(
    (path.stat().st_mtime_ns for path in _existing_gscore_paths),
    default=0,
)

_config_names = {"群分析·总览", *_NATIVE_CONFIG_PATHS}
for _config_name, _registered_config in tuple(all_config_list.items()):
    if (
        getattr(_registered_config, "plugin_name", None) in {"QQGroupDailyAnalysis", PLUGIN_NAME}
        and _config_name not in _config_names
    ):
        all_config_list.pop(_config_name, None)

gsconfig = StringConfig(
    "群分析·总览",
    GSCORE_CONFIG_PATH,
    {
        "Enabled": GsBoolConfig(
            title="启用 DailyAnalyisis",
            desc="关闭后停止命令、消息归档、定时分析和增量分析。",
            data=True,
        ),
        "ExternalWebUIEnabled": GsBoolConfig(
            title="启用外部 WebUI",
            desc="默认关闭。开启后才会挂载 DailyAnalyisis 独立 WebUI；首次访问必须设置至少 8 位密码。",
            data=False,
        ),
    },
)
gsconfig.plugin_name = PLUGIN_NAME

group_configs: dict[str, StringConfig] = {}
native_configs = {
    name: StringConfig(name, _NATIVE_CONFIG_PATHS[name], _build_native_group(keys))
    for name, keys in _NATIVE_GROUP_MEMBERS.items()
}
for _group_key in _SCHEMA:
    for _native_name, _members in _NATIVE_GROUP_MEMBERS.items():
        if _group_key in _members:
            group_configs[_group_key] = native_configs[_native_name]
            break
for _native_config in native_configs.values():
    _native_config.plugin_name = PLUGIN_NAME

legacy_group_configs: dict[str, StringConfig] = {}
for _group_key, _group in _SCHEMA.items():
    _legacy_path = _GROUP_CONFIG_PATHS[_group_key]
    if not isinstance(_group, dict) or not _legacy_path.exists():
        continue
    _legacy_config = StringConfig(
        _GROUP_CONFIG_NAMES.get(_group_key, f"群分析·{_group_key}"),
        _legacy_path,
        _build_gscore_group(_group_key, _group),
    )
    _legacy_config.plugin_name = PLUGIN_NAME
    legacy_group_configs[_group_key] = _legacy_config


def _config_for_path(path: tuple[str, ...]) -> StringConfig:
    return group_configs[path[0]]


def _migrate_legacy_gscore_config() -> None:
    legacy_mapping = {
        "DefaultDays": "basic.analysis_days",
        "MaxMessages": "basic.max_messages",
        "MinMessages": "basic.min_messages_threshold",
        "OutputFormats": "basic.output_format",
        "ScheduleTimes": "auto_analysis.auto_analysis_time",
    }
    legacy_provider_fields = {
        "llm_provider_id",
        "topic_provider_id",
        "user_title_provider_id",
        "golden_quote_provider_id",
        "quality_provider_id",
        "drawing_prompt_provider_id",
    }
    changed = False
    for group_key, legacy_config in legacy_group_configs.items():
        group_configs[group_key].migrate_from(legacy_config)
    native_configs["DailyAnalyisis LLM配置"].migrate_from(
        [
            native_configs["DailyAnalyisis基础配置"],
            native_configs["DailyAnalyisis展示配置"],
        ]
    )
    for group_config in native_configs.values():
        group_config.migrate_from(gsconfig)
    for config in legacy_group_configs.values():
        for field_name in legacy_provider_fields:
            for key in (field_name, f"llm.{field_name}"):
                if key in config.config:
                    config.config.pop(key)
                    changed = True
        if changed:
            config.sort_config()
    for old_key, new_key in legacy_mapping.items():
        target_config = _config_for_path(tuple(new_key.split(".")))
        if old_key not in gsconfig.config or new_key not in target_config.config:
            continue
        _assign_gscore_value(
            target_config.config[new_key],
            deepcopy(gsconfig.config[old_key].data),
        )
        target_config.write_config()
        gsconfig.config.pop(old_key)
        changed = True
    stale_keys = [
        key
        for key in gsconfig.config
        if key not in {"Enabled", "ExternalWebUIEnabled"}
    ]
    if stale_keys:
        for key in stale_keys:
            gsconfig.config.pop(key)
        changed = True
    if changed:
        gsconfig.sort_config()
    for legacy_config in legacy_group_configs.values():
        all_config_list.pop(legacy_config.config_name, None)


def _get_nested(data: dict, path: tuple[str, ...]) -> object:
    current: object = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _set_nested(data: dict, path: tuple[str, ...], value: object) -> None:
    current = data
    for key in path[:-1]:
        child = current.get(key)
        if not isinstance(child, dict):
            child = {}
            current[key] = child
        current = child
    current[path[-1]] = deepcopy(value)


def _to_gscore_value(path: tuple[str, ...], value: object, spec: dict) -> object:
    field_type = spec.get("type")
    if field_type == "template_list" and isinstance(value, list):
        return deepcopy(value)
    if ".".join(path) in _STRUCTURED_PATHS:
        return json.dumps(value, ensure_ascii=False, indent=2)
    if field_type == "list":
        return [str(item) for item in value] if isinstance(value, list) else []
    if field_type == "bool":
        return bool(value)
    if field_type == "int":
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        if isinstance(value, float):
            return int(value)
        return 0
    if field_type == "float":
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
        return 0.0
    return str(value or "")


def _from_gscore_value(path: tuple[str, ...], value: object) -> object:
    if ".".join(path) in _TEMPLATE_LIST_PATHS and isinstance(value, list):
        return deepcopy(value)
    if ".".join(path) not in _STRUCTURED_PATHS:
        return deepcopy(value)
    try:
        return json.loads(str(value))
    except json.JSONDecodeError:
        logger.warning("DailyAnalyisis 配置 %s 不是有效 JSON，已保留原值", ".".join(path))
        return None


def _assign_gscore_value(field: GSC, value: object) -> bool:
    if isinstance(field, GsRepeatGroupConfig) and isinstance(value, list):
        field.data = _repeat_group_rows(value, field.template)
        return True
    if isinstance(field, GsBoolConfig) and isinstance(value, bool):
        field.data = value
        return True
    if isinstance(field, GsIntConfig) and isinstance(value, int) and not isinstance(value, bool):
        field.data = value
        return True
    if isinstance(field, GsFloatConfig) and isinstance(value, (int, float)) and not isinstance(value, bool):
        field.data = float(value)
        return True
    if isinstance(field, GsListStrConfig) and isinstance(value, list):
        field.data = [str(item) for item in value]
        return True
    if isinstance(field, GsStrConfig) and isinstance(value, str):
        field.data = value
        return True
    return False


def _sync_gscore_from_config(data: dict) -> None:
    changed_configs: dict[str, StringConfig] = {}
    for path, spec in _SCHEMA_FIELDS:
        key = ".".join(path)
        group_config = _config_for_path(path)
        if key not in group_config.config:
            continue
        value = _to_gscore_value(path, _get_nested(data, path), spec)
        field = group_config.config[key]
        if field.data != value:
            if _assign_gscore_value(field, value):
                changed_configs[group_config.config_name] = group_config
    webui = data.get("webui")
    external_enabled = (
        bool(webui.get("external_enabled", False))
        if isinstance(webui, dict)
        else False
    )
    external_field = gsconfig.config.get("ExternalWebUIEnabled")
    if external_field is not None and external_field.data != external_enabled:
        if _assign_gscore_value(external_field, external_enabled):
            changed_configs[gsconfig.config_name] = gsconfig
    for group_config in changed_configs.values():
        group_config.write_config()


def _apply_gscore_to_config(data: dict) -> None:
    for path, _spec in _SCHEMA_FIELDS:
        key = ".".join(path)
        group_config = _config_for_path(path)
        if key not in group_config.config:
            continue
        field = group_config.config[key]
        if isinstance(field, GsRepeatGroupConfig):
            value = _repeat_group_values(field.data)
        else:
            value = _from_gscore_value(path, field.data)
        if value is not None:
            _set_nested(data, path, value)
    external_field = gsconfig.config.get("ExternalWebUIEnabled")
    if external_field is not None:
        _set_nested(
            data,
            ("webui", "external_enabled"),
            bool(external_field.data),
        )


def _write_config(data: dict) -> None:
    webui = data.get("webui")
    if isinstance(webui, dict):
        password = str(webui.get("password", "")).strip()
        if password == "********" and CONFIG_PATH.exists():
            try:
                previous = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                previous_webui = previous.get("webui", {})
                previous_password = (
                    previous_webui.get("password", "")
                    if isinstance(previous_webui, dict)
                    else ""
                )
                if str(previous_password).startswith("pbkdf2_sha256$"):
                    password = str(previous_password)
                    webui["password"] = password
            except (OSError, json.JSONDecodeError):
                pass
        if password and not password.startswith("pbkdf2_sha256$"):
            webui["password"] = WebUIAuthenticator.hash_password(password)
    temporary = CONFIG_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(CONFIG_PATH)
    _sync_gscore_from_config(data)


def load_config() -> PluginConfig:
    config_exists = CONFIG_PATH.exists()
    config_mtime = CONFIG_PATH.stat().st_mtime_ns if config_exists else 0
    try:
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raw = {}
    merged = _merge_defaults(raw, _DEFAULTS)
    assert isinstance(merged, dict)
    llm_config = merged.get("llm")
    if isinstance(llm_config, dict):
        for field_name in (
            "llm_provider_id",
            "topic_provider_id",
            "user_title_provider_id",
            "golden_quote_provider_id",
            "quality_provider_id",
            "drawing_prompt_provider_id",
        ):
            llm_config.pop(field_name, None)
    if _GSCORE_CONFIG_EXISTED and _GSCORE_CONFIG_MTIME > config_mtime:
        _apply_gscore_to_config(merged)
    else:
        _sync_gscore_from_config(merged)
    webui = merged.get("webui")
    if isinstance(webui, dict):
        password = str(webui.get("password", "")).strip()
        if password and not password.startswith("pbkdf2_sha256$"):
            webui["password"] = WebUIAuthenticator.hash_password(password)
    _write_config(merged)
    return PluginConfig(merged, save_callback=_write_config)


_migrate_legacy_gscore_config()


__all__ = [
    "CONFIG_PATH",
    "DATA_DIR",
    "GSCORE_CONFIG_PATH",
    "group_configs",
    "gsconfig",
    "load_config",
    "load_schema",
]
