"""Testes para simulation_army_v2.costs."""
from simulation_army_v2.costs import PRICING, calculate_cost_usd, calculate_run_cost


class TestCalculateCostUsd:
    def test_free_model_returns_zero(self):
        assert calculate_cost_usd("kilo/tencent/hy3:free", 1000, 500) == 0.0

    def test_free_model_with_zero_tokens(self):
        assert calculate_cost_usd("glm-5-2", 0, 0) == 0.0

    def test_paid_model_command_r_plus(self):
        # command-r-plus-08-2024: $2.5/1M input, $10.0/1M output
        # 1000 input + 500 output = 0.0025 + 0.005 = 0.0075
        cost = calculate_cost_usd("command-r-plus-08-2024", 1000, 500)
        assert cost is not None
        assert abs(cost - 0.0075) < 1e-6

    def test_paid_model_gemini_flash(self):
        # gemini-2.5-flash: $0.075/1M input, $0.30/1M output
        # 10000 input + 2000 output = 0.00075 + 0.0006 = 0.00135
        cost = calculate_cost_usd("gemini-2.5-flash", 10000, 2000)
        assert cost is not None
        assert abs(cost - 0.00135) < 1e-6

    def test_none_tokens_returns_none(self):
        assert calculate_cost_usd("command-r-plus-08-2024", None, 500) is None
        assert calculate_cost_usd("command-r-plus-08-2024", 1000, None) is None

    def test_unknown_model_returns_none(self):
        assert calculate_cost_usd("unknown/model", 1000, 500) is None

    def test_all_22_models_in_pricing(self):
        """Todos os 22 modelos do scenario v4 devem estar na tabela."""
        modelos_v4 = [
            "command-r-plus-08-2024", "command-a-03-2025",
            "llama-3.3-70b-versatile", "qwen/qwen3.6-27b",
            "gemini-2.5-flash", "deepseek-ai/deepseek-v4-flash",
            "Meta-Llama-3.3-70B-Instruct", "tencent/hy3:free",
            "kilo-auto/free", "deepseek-ai/DeepSeek-V3",
            "kilo/cohere/north-mini-code:free", "kilo/kilo-auto/free",
            "kilo/kwaipilot/kat-coder-pro-v2.5:free",
            "kilo/nvidia/nemotron-3-super-120b-a12b:free",
            "kilo/nvidia/nemotron-3-ultra-550b-a55b:free",
            "kilo/openrouter/free", "kilo/poolside/laguna-m.1:free",
            "kilo/poolside/laguna-xs-2.1:free", "kilo/stepfun/step-3.7-flash:free",
            "kilo/tencent/hy3:free", "glm-5-2", "swe-1-7",
        ]
        for model in modelos_v4:
            assert model in PRICING, f"modelo {model} nao esta na tabela PRICING"


class TestCalculateRunCost:
    def test_empty_list(self):
        result = calculate_run_cost([])
        assert result["custo_total_usd"] == 0.0
        assert result["custo_por_modelo"] == {}

    def test_mixed_models(self):
        metadados = [
            {"modelo": "command-r-plus-08-2024", "prompt_tokens": 1000, "completion_tokens": 500},
            {"modelo": "kilo/tencent/hy3:free", "prompt_tokens": 10000, "completion_tokens": 5000},
            {"modelo": "command-r-plus-08-2024", "prompt_tokens": 2000, "completion_tokens": 1000},
        ]
        result = calculate_run_cost(metadados)
        # command-r-plus: 2 requests, 3000 input + 1500 output
        # = 0.0075 + 0.015 = 0.0225
        assert abs(result["custo_total_usd"] - 0.0225) < 1e-6
        assert abs(result["custo_por_modelo"]["command-r-plus-08-2024"] - 0.0225) < 1e-6
        # kilo free = 0
        assert result["custo_por_modelo"]["kilo/tencent/hy3:free"] == 0.0

    def test_skips_errors(self):
        metadados = [
            {"modelo": "command-r-plus-08-2024", "prompt_tokens": 1000, "completion_tokens": 500},
            {"modelo": "gemini-2.5-flash", "erro": "HTTP 503"},
        ]
        result = calculate_run_cost(metadados)
        # so command-r-plus conta
        assert abs(result["custo_total_usd"] - 0.0075) < 1e-6
        assert "gemini-2.5-flash" not in result["custo_por_modelo"]

    def test_none_tokens_skipped(self):
        metadados = [
            {"modelo": "glm-5-2", "prompt_tokens": None, "completion_tokens": None},
            {"modelo": "command-r-plus-08-2024", "prompt_tokens": 1000, "completion_tokens": 500},
        ]
        result = calculate_run_cost(metadados)
        # so command-r-plus conta (glm-5-2 tem tokens None)
        assert abs(result["custo_total_usd"] - 0.0075) < 1e-6
        assert "glm-5-2" not in result["custo_por_modelo"]
