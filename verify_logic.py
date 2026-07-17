"""Quick import check and logic verification — no pytest required."""
import sys
import os
sys.path.insert(0, r"c:\Users\jagta\phoenix\phoenix-stadium")

# Activate venv
venv_site = r"c:\Users\jagta\phoenix\phoenix-stadium\.venv\Lib\site-packages"
sys.path.insert(0, venv_site)

errors = []

try:
    from app.core.schemas import Language, Persona, AccessibilityNeed, GateStatus, WaitEstimate, UserQuery, ResolvedContext
    print("✅ schemas.py imports OK")
    # Verify AR is gone
    langs = [l.value for l in Language]
    assert "ar" not in langs, f"Arabic still in Language enum: {langs}"
    print(f"✅ Languages: {langs}")
except Exception as e:
    errors.append(f"schemas.py: {e}")
    print(f"❌ {e}")

try:
    from app.core.context_engine import (
        _pseudo_multiplier, _live_turnstile_overrides, predict_wait, 
        live_gate_snapshot, live_all_gate_predictions, GATES
    )
    print("✅ context_engine.py imports OK")
    
    # Test lru_cache API
    _pseudo_multiplier.cache_clear()
    v1 = _pseudo_multiplier("A", 12345)
    v2 = _pseudo_multiplier("A", 12345)
    assert v1 == v2
    assert _pseudo_multiplier.cache_info().hits >= 1
    print(f"✅ lru_cache works: v1={v1:.4f}, hits={_pseudo_multiplier.cache_info().hits}")
    
    # Test gate B IoT override and utilization
    _live_turnstile_overrides.clear()
    _live_turnstile_overrides["B"] = {
        "arrivals_per_min": 10.5,
        "capacity_per_min": 2.5,
        "servers_open": 5,
    }
    snapshot = live_gate_snapshot()
    gate_b = snapshot["B"]
    wait_b = predict_wait(gate_b)
    expected_rho = round(10.5 / (5 * 2.5), 3)
    assert wait_b.utilization == expected_rho, f"Expected utilization={expected_rho}, got {wait_b.utilization}"
    print(f"✅ Gate B utilization after override: {wait_b.utilization} (expected {expected_rho})")
    _live_turnstile_overrides.clear()
    
except Exception as e:
    errors.append(f"context_engine.py: {e}")
    print(f"❌ {e}")

try:
    from app.core.llm import MockLLM, get_llm
    print("✅ llm.py imports OK")
    
    # Verify no Arabic template
    from app.core.llm import _TEMPLATES, _CONGESTION_LABELS
    for intent, langs_dict in _TEMPLATES.items():
        for lang in langs_dict:
            assert lang.value != "ar", f"Arabic in template for intent {intent}"
    print("✅ No Arabic in templates")
    
    # Test Spanish template
    gate = GateStatus(gate_id="A", name="Gate A — North", capacity_per_min=3.2, arrivals_per_min=1.0, servers_open=3)
    wait = WaitEstimate(gate_id="A", predicted_wait_minutes=4.0, utilization=0.3, congestion_level="low", server_farm_saturated=False)
    ctx = ResolvedContext(
        intent="find_gate", recommended_gate=gate, wait_estimate=wait,
        accessible_route_available=True, safety_notice=None,
        sanitized_user_text="which gate", language=Language.ES
    )
    reply = MockLLM().phrase(ctx)
    assert "Gate A" in reply.text
    assert len(reply.text) > 10
    print(f"✅ Spanish template: '{reply.text[:60]}...'")
    
except Exception as e:
    errors.append(f"llm.py: {e}")
    print(f"❌ {e}")

try:
    from app.core.security import sanitize_text
    dirty = "how is gate B; -- rm -rf /; | cat /etc/passwd"
    clean = sanitize_text(dirty)
    assert ";" not in clean
    assert "--" not in clean
    assert "|" not in clean
    assert "&" not in clean
    assert "$" not in clean
    assert "`" not in clean
    assert "rm -rf" in clean
    print(f"✅ sanitize_text works: '{clean}'")
except Exception as e:
    errors.append(f"security.py: {e}")
    print(f"❌ {e}")

try:
    from app.core.context_engine import predict_wait
    from app.core.schemas import GateStatus
    overloaded = GateStatus(gate_id="X", name="Overloaded", capacity_per_min=1.0, arrivals_per_min=100.0, servers_open=1)
    est = predict_wait(overloaded)
    assert est.predicted_wait_minutes == 99.0
    assert est.congestion_level == "critical"
    print(f"✅ Wait ceiling clamp: {est.predicted_wait_minutes} min, {est.congestion_level}")
except Exception as e:
    errors.append(f"predict_wait clamp: {e}")
    print(f"❌ {e}")

print("\n" + "="*50)
if errors:
    print(f"❌ {len(errors)} ERRORS:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("✅ ALL CHECKS PASSED")
