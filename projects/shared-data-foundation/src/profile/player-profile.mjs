export const PROFILE_KEY = "dragonfire.playerProfile.v1";
export const PROFILE_VERSION = 2;

const clamp = (value, min, max, fallback) => {
  const number = Number(value);
  return Number.isFinite(number) ? Math.min(max, Math.max(min, Math.round(number))) : fallback;
};

export function habitAbilities(dragon) {
  return (dragon?.abilities || []).filter(ability => ability.kind === "habit");
}

export function preferredTroops(dragon) {
  const troops = dragon?.troop_affinities?.positive;
  return Array.isArray(troops) ? [...new Set(troops.map(String))] : [];
}

export function defaultEntry(dragon, assumed = true) {
  return {
    owned: true,
    level: 50,
    stars: 10,
    preferred_troops: preferredTroops(dragon),
    habit_levels: Object.fromEntries(habitAbilities(dragon).map(ability => [ability.client_key, 5])),
    assumed,
  };
}

export function normalizeProfile(raw, dragons) {
  const source = raw && typeof raw === "object" ? raw : {};
  const sourceDragons = source.dragons && typeof source.dragons === "object" ? source.dragons : {};
  const normalized = {
    version: PROFILE_VERSION,
    updated_at: source.updated_at || null,
    dragons: {},
  };
  for (const dragon of dragons.filter(item => item.lifecycle !== "staged")) {
    const incoming = sourceDragons[dragon.slug];
    const fallback = defaultEntry(dragon, !incoming);
    const habits = incoming?.habit_levels && typeof incoming.habit_levels === "object" ? incoming.habit_levels : {};
    normalized.dragons[dragon.slug] = {
      owned: incoming?.owned == null ? fallback.owned : Boolean(incoming.owned),
      level: clamp(incoming?.level, 1, 50, fallback.level),
      stars: clamp(incoming?.stars, 1, 10, fallback.stars),
      preferred_troops: fallback.preferred_troops,
      habit_levels: Object.fromEntries(habitAbilities(dragon).map(ability => [ability.client_key, clamp(habits[ability.client_key], 0, 5, fallback.habit_levels[ability.client_key])])),
      assumed: incoming?.assumed == null ? fallback.assumed : Boolean(incoming.assumed),
    };
  }
  return normalized;
}

export function loadProfile(dragons, storage = globalThis.localStorage) {
  let raw = null;
  try { raw = JSON.parse(storage?.getItem(PROFILE_KEY) || "null"); } catch { raw = null; }
  return normalizeProfile(raw, dragons);
}

export function saveProfile(profile, dragons, storage = globalThis.localStorage) {
  const normalized = normalizeProfile(profile, dragons);
  normalized.updated_at = new Date().toISOString();
  for (const entry of Object.values(normalized.dragons)) entry.assumed = false;
  storage?.setItem(PROFILE_KEY, JSON.stringify(normalized));
  return normalized;
}

export function rosterEntries(profile) {
  return Object.entries(profile.dragons).filter(([, entry]) => entry.owned).map(([slug, entry]) => ({ slug, ...entry }));
}

export function habitSummary(dragon, entry) {
  const levels = habitAbilities(dragon).map(ability => entry?.habit_levels?.[ability.client_key]);
  return levels.length ? levels.map(value => value ?? "?").join("/") : "—";
}

export function profileSummary(profile) {
  const entries = Object.values(profile.dragons);
  const owned = entries.filter(entry => entry.owned);
  const assumed = owned.filter(entry => entry.assumed).length;
  return { owned: owned.length, total: entries.length, assumed };
}

export function mountProfileManager({ dragons, getProfile, setProfile, onSave = () => {} }) {
  const host = document.createElement("div");
  host.className = "profile-manager";
  host.innerHTML = `<div class="profile-strip"><div><strong>Your local roster</strong><span id="profile-summary"></span></div><button type="button" id="profile-open">Manage profile</button></div>
    <dialog id="profile-dialog"><form method="dialog" class="profile-dialog-card"><div class="profile-heading"><div><p>LOCAL PLAYER PROFILE</p><h2>Roster and progression</h2></div><button value="cancel" aria-label="Close profile">Close</button></div><p class="profile-note">Saved only in this browser. Habit levels are retained for context; current recommendations use verified level and Star gates rather than estimating numeric power.</p><div class="profile-actions"><button type="button" id="profile-all">Own all</button><button type="button" id="profile-none">Own none</button><button type="button" id="profile-export">Export JSON</button><button type="button" id="profile-import">Import JSON</button><input id="profile-file" type="file" accept="application/json" hidden></div><div class="profile-table"><div class="profile-row profile-labels"><span>Owned</span><span>Dragon</span><span>Level</span><span>Stars</span><span>Habit levels</span></div><div id="profile-rows"></div></div><div class="profile-footer"><span id="profile-message" aria-live="polite"></span><button type="button" class="profile-save" id="profile-save">Save profile</button></div></form></dialog>`;
  document.querySelector("main").prepend(host);
  const dialog = host.querySelector("#profile-dialog");
  const rows = host.querySelector("#profile-rows");
  const message = host.querySelector("#profile-message");

  function updateSummary() {
    const summary = profileSummary(getProfile());
    host.querySelector("#profile-summary").textContent = `${summary.owned} of ${summary.total} dragons owned${summary.assumed ? " · starter assumptions active" : ""}`;
  }

  function renderRows() {
    const profile = getProfile();
    rows.innerHTML = dragons.filter(item => item.lifecycle !== "staged").sort((a, b) => a.name.localeCompare(b.name)).map(dragon => {
      const entry = profile.dragons[dragon.slug];
      return `<div class="profile-row" data-slug="${dragon.slug}"><input class="profile-owned" type="checkbox" aria-label="Own ${dragon.name}" ${entry.owned ? "checked" : ""}><strong>${dragon.name}</strong><input class="profile-level" type="number" min="1" max="50" value="${entry.level}" aria-label="${dragon.name} level"><input class="profile-stars" type="number" min="1" max="10" value="${entry.stars}" aria-label="${dragon.name} Star Rank"><input class="profile-habits" value="${habitSummary(dragon, entry)}" aria-label="${dragon.name} Habit levels" title="Slash-separated levels in displayed ability order"></div>`;
    }).join("");
  }

  function readRows() {
    const profile = structuredClone(getProfile());
    for (const row of rows.querySelectorAll(".profile-row")) {
      const dragon = dragons.find(item => item.slug === row.dataset.slug);
      const entry = profile.dragons[row.dataset.slug];
      entry.owned = row.querySelector(".profile-owned").checked;
      entry.level = clamp(row.querySelector(".profile-level").value, 1, 50, entry.level);
      entry.stars = clamp(row.querySelector(".profile-stars").value, 1, 10, entry.stars);
      const values = row.querySelector(".profile-habits").value.split(/[\/,\s]+/).filter(Boolean);
      habitAbilities(dragon).forEach((ability, index) => { entry.habit_levels[ability.client_key] = clamp(values[index], 0, 5, entry.habit_levels[ability.client_key]); });
    }
    return profile;
  }

  host.querySelector("#profile-open").addEventListener("click", () => { renderRows(); message.textContent = ""; dialog.showModal(); });
  host.querySelector("#profile-all").addEventListener("click", () => rows.querySelectorAll(".profile-owned").forEach(input => { input.checked = true; }));
  host.querySelector("#profile-none").addEventListener("click", () => rows.querySelectorAll(".profile-owned").forEach(input => { input.checked = false; }));
  host.querySelector("#profile-save").addEventListener("click", () => { setProfile(saveProfile(readRows(), dragons)); updateSummary(); dialog.close(); onSave(); });
  host.querySelector("#profile-export").addEventListener("click", () => {
    const blob = new Blob([JSON.stringify(readRows(), null, 2)], { type: "application/json" });
    const link = Object.assign(document.createElement("a"), { href: URL.createObjectURL(blob), download: "dragonfire-player-profile.json" });
    link.click(); URL.revokeObjectURL(link.href); message.textContent = "Profile exported.";
  });
  host.querySelector("#profile-import").addEventListener("click", () => host.querySelector("#profile-file").click());
  host.querySelector("#profile-file").addEventListener("change", async event => {
    try { setProfile(normalizeProfile(JSON.parse(await event.target.files[0].text()), dragons)); renderRows(); message.textContent = "Imported. Review and save to apply."; }
    catch { message.textContent = "That file is not a valid Dragonfire profile."; }
    event.target.value = "";
  });
  updateSummary();
  return { updateSummary };
}
