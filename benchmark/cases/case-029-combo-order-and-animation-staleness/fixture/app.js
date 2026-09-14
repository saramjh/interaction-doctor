// Small combo-attack game. pressDirection() feeds a directional input
// buffer; a matching three-input sequence triggers the special move.
// The move's attack commits to a target at trigger time, but its damage
// is only applied later, when completeAttackAnimation() is called.
const COMBO_WINDOW_MS = 500;
const ATTACK_DAMAGE = 10;

function createComboGame() {
  const state = {
    now: 0,
    recentInputBuffer: [],
    currentTarget: null,
    triggerCount: 0,
    pendingAttack: null,
    entities: {
      T1: { health: 100 },
      T2: { health: 100 },
      T3: { health: 100 },
    },
  };

  function pressDirection(direction) {
    state.recentInputBuffer.push({ direction, timestamp: state.now });
    state.recentInputBuffer = state.recentInputBuffer.filter(
      (e) => state.now - e.timestamp <= COMBO_WINDOW_MS
    );
    const seen = new Set(state.recentInputBuffer.map((e) => e.direction));
    if (seen.has('D1') && seen.has('D2') && seen.has('D3')) {
      triggerCombo();
    }
  }

  function triggerCombo() {
    state.triggerCount += 1;
    state.pendingAttack = {};
    state.recentInputBuffer = [];
  }

  function setCurrentTarget(id) {
    state.currentTarget = id;
  }

  function advanceTime(ms) {
    state.now += ms;
  }

  function completeAttackAnimation() {
    if (!state.pendingAttack) return;
    const target = state.currentTarget;
    if (state.entities[target]) {
      state.entities[target].health -= ATTACK_DAMAGE;
    }
    state.pendingAttack = null;
  }

  function getTriggerCount() {
    return state.triggerCount;
  }

  function getEntityHealth(id) {
    return state.entities[id] ? state.entities[id].health : null;
  }

  return {
    state,
    pressDirection,
    setCurrentTarget,
    advanceTime,
    completeAttackAnimation,
    getTriggerCount,
    getEntityHealth,
  };
}

module.exports = { createComboGame };
