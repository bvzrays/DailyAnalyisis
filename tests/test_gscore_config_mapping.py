from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import astrbot.api
import astrbot.api.star
from gsuid_core import data_store
from gsuid_core.utils.plugins_config.gs_config import all_config_list


PLUGIN_CONFIG_PATH = (
    Path(__file__).resolve().parents[1] / "QQGroupDailyAnalysis" / "plugin_config.py"
)


class _AstrBotConfig(dict):
    def __init__(self, *args, save_callback=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.save_callback = save_callback

    def save_config(self):
        if self.save_callback is not None:
            self.save_callback(dict(self))


def _load_plugin_config(tmp_path: Path, monkeypatch):
    all_config_list.pop("QQGroupDailyAnalysis", None)
    monkeypatch.setattr(data_store, "get_res_path", lambda *args: tmp_path)
    monkeypatch.setattr(astrbot.api, "AstrBotConfig", _AstrBotConfig)
    monkeypatch.setattr(
        astrbot.api.star,
        "StarTools",
        SimpleNamespace(set_data_dir=lambda _path: None),
    )
    spec = importlib.util.spec_from_file_location("qqgda_plugin_config_test", PLUGIN_CONFIG_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_all_schema_fields_are_mapped_to_gscore(tmp_path: Path, monkeypatch):
    module = _load_plugin_config(tmp_path, monkeypatch)
    mapped_keys = {
        key
        for key in module.gsconfig.config_list
        if key != "Enabled" and not key.startswith("__group__.")
    }
    schema_keys = {".".join(path) for path, _spec in module._SCHEMA_FIELDS}

    assert len(schema_keys) == 101
    assert mapped_keys == schema_keys
    assert "DefaultDays" not in module.gsconfig.config
    assert "ConfigFile" not in module.gsconfig.config


def test_plugin_and_gscore_configs_round_trip(tmp_path: Path, monkeypatch):
    module = _load_plugin_config(tmp_path, monkeypatch)
    config = module.load_config()
    config["basic"]["analysis_days"] = 7
    config["llm"]["topic_provider_id"] = "gscore"
    config["daily_comic"]["comic_characters"] = [{"name": "测试角色"}]
    config.save_config()

    assert module.gsconfig.get_config("basic.analysis_days").data == 7
    assert module.gsconfig.get_config("llm.topic_provider_id").data == "gscore"
    assert "测试角色" in module.gsconfig.get_config("daily_comic.comic_characters").data

    restored = module.default_config()
    module._apply_gscore_to_config(restored)

    assert restored["basic"]["analysis_days"] == 7
    assert restored["llm"]["topic_provider_id"] == "gscore"
    assert restored["daily_comic"]["comic_characters"] == [{"name": "测试角色"}]
