import pytest
from unittest.mock import MagicMock
from game.commands import CommandHandler
from game.engine import GameEngine

@pytest.fixture
def command_handler():
    mock_engine = MagicMock(spec=GameEngine)
    return CommandHandler(mock_engine), mock_engine

def test_handle_input_variations(command_handler):
    handler, mock_engine = command_handler
    
    # 测试带尖括号的参数
    handler.handle("take <Iron Sword>")
    mock_engine.take_item.assert_called_with("iron sword")
    
    # 测试黏连指令
    handler.handle("takeiron sword")
    mock_engine.take_item.assert_called_with("iron sword")
    
    # 测试简单指令
    handler.handle("north")
    mock_engine.move_player.assert_called_with("north")

def test_cmd_stats(command_handler):
    handler, mock_engine = command_handler
    mock_engine.show_stats.return_value = "Stats String"
    
    assert handler.handle("stats") == "Stats String"

def test_cmd_save_load(command_handler):
    handler, mock_engine = command_handler
    
    mock_engine.save_game.return_value = "保存成功"
    assert "成功" in handler.handle("save")
    
    mock_engine.load_game.return_value = "加载成功"
    assert "成功" in handler.handle("load")

def test_cmd_respawn(command_handler):
    handler, mock_engine = command_handler
    mock_engine.respawn.return_value = "Respawned"
    assert handler.handle("respawn") == "Respawned"

def test_cmd_help(command_handler):
    handler, _ = command_handler
    result = handler.handle("help")
    assert "MUD" in result
    assert "go" in result
