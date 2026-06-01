const DATA_URL = "./data/schools.json";
const POSTCODE_RE = /^[1-9][0-9]{3}\s?[a-z]{2}$/i;
const NL_BOUNDS = {
  minLon: 3.16,
  maxLon: 7.28,
  minLat: 50.74,
  maxLat: 53.62
};

const SAMPLE_DATA = {
  generatedAt: new Date().toISOString(),
  sources: [],
  stats: { schoolCount: 3, adviceRatioCount: 3, originRatioCount: 3, withCoordinates: 3 },
  schools: [
    {
      id: "00AP-00",
      brin: "00AP",
      branch: "00",
      name: "WereldWijs",
      city: "ZOETERMEER",
      municipality: "Zoetermeer",
      province: "Zuid-Holland",
      postcode: "2716PH",
      type: "Bo",
      denomination: "Gereformeerd vrijgemaakt",
      address: "Marsmanhove 1",
      website: "",
      latitude: 52.0465,
      longitude: 4.5232,
      pupils: { min: 73, max: 82, redacted: true },
      origin: {
        year: 2025,
        postcode4: "2716",
        totalMin: 74,
        totalMax: 83,
        localMin: 34,
        localMax: 34,
        localRatioMin: 0.41,
        localRatioMax: 0.46,
        redacted: true,
        top: [
          { postcode4: "2716", min: 34, max: 34, ratioMin: 0.41, ratioMax: 0.46, redacted: false },
          { postcode4: "2717", min: 16, max: 16, ratioMin: 0.19, ratioMax: 0.22, redacted: false },
          { postcode4: "2721", min: 8, max: 8, ratioMin: 0.1, ratioMax: 0.11, redacted: false }
        ]
      },
      advice: {
        totalMin: 10,
        totalMax: 25,
        vwoMin: 1,
        vwoMax: 4,
        havoVwoMin: 1,
        havoVwoMax: 4,
        vwoEligibleMin: 2,
        vwoEligibleMax: 8,
        redacted: true
      }
    },
    {
      id: "00AR-00",
      brin: "00AR",
      branch: "00",
      name: "BS De Maasparel",
      city: "STEVENSWEERT",
      municipality: "Maasgouw",
      province: "Limburg",
      postcode: "6107AW",
      type: "Bo",
      denomination: "Rooms-Katholiek",
      address: "Jan van Steffeswertplein 1",
      website: "",
      latitude: 51.1317,
      longitude: 5.8494,
      pupils: { min: 150, max: 160, redacted: true },
      origin: {
        year: 2025,
        postcode4: "6107",
        totalMin: 150,
        totalMax: 160,
        localMin: 84,
        localMax: 84,
        localRatioMin: 0.53,
        localRatioMax: 0.56,
        redacted: true,
        top: [
          { postcode4: "6107", min: 84, max: 84, ratioMin: 0.53, ratioMax: 0.56, redacted: false },
          { postcode4: "6109", min: 21, max: 21, ratioMin: 0.13, ratioMax: 0.14, redacted: false },
          { postcode4: "6017", min: 12, max: 12, ratioMin: 0.08, ratioMax: 0.08, redacted: false }
        ]
      },
      advice: {
        totalMin: 18,
        totalMax: 31,
        vwoMin: 1,
        vwoMax: 4,
        havoVwoMin: 0,
        havoVwoMax: 0,
        vwoEligibleMin: 1,
        vwoEligibleMax: 4,
        redacted: true
      }
    },
    {
      id: "00AZ-00",
      brin: "00AZ",
      branch: "00",
      name: "De Stapsteen",
      city: "BLESKENSGRAAF CA",
      municipality: "Molenlanden",
      province: "Zuid-Holland",
      postcode: "2971AR",
      type: "Bo",
      denomination: "Openbaar",
      address: "Dorpsstraat 10",
      website: "",
      latitude: 51.8726,
      longitude: 4.7837,
      pupils: { min: 115, max: 124, redacted: true },
      origin: {
        year: 2025,
        postcode4: "2971",
        totalMin: 116,
        totalMax: 125,
        localMin: 66,
        localMax: 66,
        localRatioMin: 0.53,
        localRatioMax: 0.57,
        redacted: true,
        top: [
          { postcode4: "2971", min: 66, max: 66, ratioMin: 0.53, ratioMax: 0.57, redacted: false },
          { postcode4: "2973", min: 24, max: 24, ratioMin: 0.19, ratioMax: 0.21, redacted: false },
          { postcode4: "2957", min: 9, max: 9, ratioMin: 0.07, ratioMax: 0.08, redacted: false }
        ]
      },
      advice: {
        totalMin: 7,
        totalMax: 31,
        vwoMin: 1,
        vwoMax: 4,
        havoVwoMin: 1,
        havoVwoMax: 4,
        vwoEligibleMin: 2,
        vwoEligibleMax: 8,
        redacted: true
      }
    }
  ]
};

const state = {
  data: SAMPLE_DATA,
  schools: SAMPLE_DATA.schools,
  filtered: [],
  selectedId: null,
  query: "",
  radiusKm: 2.5,
  type: "all",
  sort: "vwo",
  includeHavoVwo: false,
  center: null,
  centerSource: "",
  mapInstance: null,
  mapMarkers: null,
  mapRadius: null,
  distributionMapInstance: null,
  distributionMarkers: null,
  distributionRadius: null,
  hoveredMapId: null,
  loadError: false
};

const els = {
  form: document.querySelector("#filters"),
  search: document.querySelector("#searchInput"),
  radius: document.querySelector("#radiusSelect"),
  type: document.querySelector("#typeSelect"),
  sort: document.querySelector("#sortSelect"),
  include: document.querySelector("#includeHavoVwo"),
  list: document.querySelector("#schoolList"),
  summary: document.querySelector("#resultSummary"),
  stats: document.querySelector("#statsGrid"),
  median: document.querySelector("#medianMetric"),
  map: document.querySelector("#realMap"),
  mapFallback: document.querySelector("#mapCanvas"),
  distributionMap: document.querySelector("#distributionMap"),
  scatter: document.querySelector("#scatterCanvas"),
  detail: document.querySelector("#detailPanel"),
  mapStatus: document.querySelector("#mapStatus"),
  sourceBadge: document.querySelector("#sourceBadge")
};

const mapCtx = els.mapFallback.getContext("2d");
const scatterCtx = els.scatter.getContext("2d");

init();

async function init() {
  await loadData();
  hydrateControlsFromUrl();
  bindEvents();
  await updateCenter();
  applyFilters();
  window.addEventListener("resize", debounce(renderVisuals, 120));
}

async function loadData() {
  try {
    const response = await fetch(DATA_URL, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    state.data = data;
    state.schools = Array.isArray(data.schools) ? data.schools : [];
    state.loadError = false;
    const generated = data.generatedAt ? new Date(data.generatedAt).toLocaleDateString("nl-NL") : "onbekend";
    els.sourceBadge.textContent = `DUO ${generated}`;
  } catch (error) {
    state.loadError = true;
    state.data = SAMPLE_DATA;
    state.schools = SAMPLE_DATA.schools;
    els.sourceBadge.textContent = "Voorbeeld";
  }
}

function bindEvents() {
  els.form.addEventListener("submit", (event) => {
    event.preventDefault();
  });

  els.form.addEventListener("input", debounce(async () => {
    syncState();
    updateUrl();
    await updateCenter();
    applyFilters();
  }, 160));

  els.form.addEventListener("change", async () => {
    syncState();
    updateUrl();
    await updateCenter();
    applyFilters();
  });

  els.mapFallback.addEventListener("click", (event) => {
    const school = pickSchoolFromCanvas(event, els.mapFallback);
    if (school) {
      selectSchool(school.id);
    }
  });

  els.scatter.addEventListener("click", (event) => {
    const school = pickSchoolFromCanvas(event, els.scatter, true);
    if (school) {
      selectSchool(school.id);
    }
  });
}

function syncState() {
  state.query = els.search.value.trim();
  state.radiusKm = Number(els.radius.value);
  state.type = els.type.value;
  state.sort = els.sort.value;
  state.includeHavoVwo = els.include.checked;
}

function hydrateControlsFromUrl() {
  const params = new URLSearchParams(window.location.search);
  if (params.has("q")) els.search.value = params.get("q") || "";
  if (params.has("radius")) els.radius.value = params.get("radius") || els.radius.value;
  if (params.has("type")) els.type.value = params.get("type") || els.type.value;
  if (params.has("sort") && hasSelectOption(els.sort, params.get("sort"))) {
    els.sort.value = params.get("sort") || els.sort.value;
  }
  if (params.has("includeHavoVwo")) els.include.checked = params.get("includeHavoVwo") !== "false";
  syncState();
}

function updateUrl() {
  const params = new URLSearchParams();
  if (state.query) params.set("q", state.query);
  params.set("radius", String(state.radiusKm));
  params.set("type", state.type);
  params.set("sort", state.sort);
  if (state.includeHavoVwo) params.set("includeHavoVwo", "true");
  const query = params.toString();
  const nextUrl = `${window.location.pathname}${query ? `?${query}` : ""}`;
  window.history.replaceState(null, "", nextUrl);
}

async function updateCenter() {
  const query = state.query.trim();
  if (!query || state.radiusKm <= 0) {
    state.center = null;
    state.centerSource = "";
    return;
  }

  if (POSTCODE_RE.test(query)) {
    const pdokCenter = await geocodePostcode(query);
    if (pdokCenter) {
      state.center = pdokCenter;
      state.centerSource = "postcode";
      return;
    }
  }

  const localCenter = getLocalCenter(query);
  if (localCenter) {
    state.center = localCenter;
    state.centerSource = "schoollocaties";
    return;
  }

  state.center = null;
  state.centerSource = "";
}

function getLocalCenter(query) {
  const normalized = normalize(query);
  const postcode = normalizePostcode(query);
  const matches = state.schools.filter((school) => {
    if (!hasLocation(school)) return false;
    if (postcode && normalizePostcode(school.postcode) === postcode) return true;
    if (postcode && normalizePostcode(school.postcode).slice(0, 4) === postcode.slice(0, 4)) return true;
    return normalize(school.city) === normalized || normalize(school.municipality) === normalized;
  });

  if (!matches.length) return null;
  const sums = matches.reduce((acc, school) => {
    acc.lat += Number(school.latitude);
    acc.lon += Number(school.longitude);
    return acc;
  }, { lat: 0, lon: 0 });

  return {
    latitude: sums.lat / matches.length,
    longitude: sums.lon / matches.length
  };
}

async function geocodePostcode(query) {
  const postcode = normalizePostcode(query);
  const url = `https://api.pdok.nl/bzk/locatieserver/search/v3_1/free?q=${encodeURIComponent(postcode)}&fq=type:postcode&fl=centroide_ll`;
  try {
    const response = await fetch(url);
    if (!response.ok) return null;
    const data = await response.json();
    const point = data?.response?.docs?.[0]?.centroide_ll;
    const match = /POINT\(([-0-9.]+) ([-0-9.]+)\)/.exec(point || "");
    if (!match) return null;
    return { longitude: Number(match[1]), latitude: Number(match[2]) };
  } catch (error) {
    return null;
  }
}

function applyFilters() {
  const q = normalize(state.query);
  const postcode = normalizePostcode(state.query);
  const radiusSearchActive = Boolean(state.center && state.radiusKm > 0);

  state.filtered = state.schools
    .map((school) => enrichSchool(school))
    .filter((school) => {
      if (state.type !== "all" && school.type !== state.type) return false;
      if (radiusSearchActive) {
        if (!hasLocation(school)) return false;
        return school.distanceKm <= state.radiusKm;
      }
      if (q && !matchesQuery(school, q, postcode)) return false;
      return true;
    })
    .sort(compareSchools);

  if (!state.filtered.some((school) => school.id === state.selectedId)) {
    state.selectedId = state.filtered[0]?.id || null;
  }

  render();
}

function enrichSchool(school) {
  const metric = getRatioMetric(school);
  const copy = {
    ...school,
    ratio: metric,
    distanceKm: state.center && hasLocation(school)
      ? distanceKm(state.center.latitude, state.center.longitude, Number(school.latitude), Number(school.longitude))
      : null
  };
  return copy;
}

function matchesQuery(school, q, postcode) {
  if (postcode) {
    const schoolPostcode = normalizePostcode(school.postcode);
    if (schoolPostcode.startsWith(postcode.slice(0, 4))) return true;
    if (schoolPostcode === postcode) return true;
  }
  return [
    school.name,
    school.city,
    school.municipality,
    school.province,
    school.postcode,
    school.brin,
    school.denomination
  ].some((value) => normalize(value).includes(q));
}

function compareSchools(a, b) {
  if (state.sort === "distance" && state.center) {
    return nullableNumber(a.distanceKm) - nullableNumber(b.distanceKm);
  }
  if (state.sort === "satisfaction") {
    const aScore = nullableNumberDescending(a.satisfaction?.score);
    const bScore = nullableNumberDescending(b.satisfaction?.score);
      if (aScore !== bScore) return bScore - aScore;
  }
  return compareRatioRank(a, b);
}

function render() {
  renderSummary();
  renderList();
  renderDetail();
  renderVisuals();
}

function renderSummary() {
  const count = state.filtered.length;
  const withRatio = state.filtered.filter((school) => school.ratio.hasRatio).length;
  const withLocation = state.filtered.filter(hasLocation).length;
  const withHistory = state.filtered.filter(hasAdviceHistory).length;
  const withBackground = state.filtered.filter(hasBackground).length;
  const median = medianOf(state.filtered.filter((s) => s.ratio.hasRatio).map((s) => s.ratio.mid));
  const centerText = state.center
    ? `${state.radiusKm} km rond ${state.centerSource}`
    : state.query
      ? "zoekresultaten"
      : "heel Nederland";

  els.summary.textContent = state.loadError
    ? "Voorbeelddata actief. Run de DUO update voor de volledige dataset."
    : `${count.toLocaleString("nl-NL")} scholen, ${centerText}`;
  els.median.textContent = Number.isFinite(median) ? `mediaan ${formatPercent(median)}` : "--";
  els.mapStatus.textContent = state.center ? centerText : "Nederland";
  els.stats.innerHTML = `
    <div><strong>${count.toLocaleString("nl-NL")}</strong><span>gevonden</span></div>
    <div><strong>${withRatio.toLocaleString("nl-NL")}</strong><span>met ratio</span></div>
    <div><strong>${withHistory.toLocaleString("nl-NL")}</strong><span>met 5 jaar</span></div>
    <div><strong>${withBackground.toLocaleString("nl-NL")}</strong><span>met achtergrond</span></div>
    <div><strong>${withLocation.toLocaleString("nl-NL")}</strong><span>met locatie</span></div>
  `;
}

function renderList() {
  const visible = state.filtered;
  if (!visible.length) {
    els.list.innerHTML = `<div class="empty">Geen scholen gevonden voor deze filters.</div>`;
    return;
  }

  els.list.innerHTML = "";
  const fragment = document.createDocumentFragment();
  visible.forEach((school) => {
    const selectedCount = getSelectedAdviceCount(school);
    const ratioLabel = getSelectedRatioLabel();
    const qualityLabel = getRatioQualityLabel(school);
    const button = document.createElement("button");
    button.type = "button";
    button.className = `school-card${school.id === state.selectedId ? " is-selected" : ""}`;
    button.addEventListener("click", () => selectSchool(school.id));
    button.innerHTML = `
      <div class="card-top">
        <div>
          <h3 class="school-name">${escapeHtml(school.name || "Onbekende school")}</h3>
          <div class="school-place">${escapeHtml(compact([school.city, school.municipality]).join(" / "))}</div>
        </div>
        <div class="ratio">
          <strong>${formatRatio(school.ratio)}</strong>
          <span>${ratioLabel}</span>
        </div>
      </div>
      <div class="bar-track"><span class="bar-fill" style="width:${Math.max(0, Math.min(100, school.ratio.mid * 100))}%"></span></div>
      <div class="school-meta">
        <span>${escapeHtml(school.type || "PO")}</span>
        <span>${ratioLabel} ${formatRange(selectedCount.min, selectedCount.max)} / ${formatRange(school.advice?.totalMin, school.advice?.totalMax)}</span>
        <span>${formatRange(school.advice?.totalMin, school.advice?.totalMax)} adviezen</span>
        <span>${formatRange(school.pupils?.min, school.pupils?.max)} leerlingen</span>
        ${qualityLabel ? `<span class="quality-chip">${escapeHtml(qualityLabel)}</span>` : ""}
        <span>tevredenheid ${formatSatisfaction(school.satisfaction)}</span>
        ${school.distanceKm != null ? `<span>${school.distanceKm.toFixed(1)} km</span>` : ""}
      </div>
      ${renderBackgroundSummary(school)}
      ${renderOriginSummary(school)}
    `;
    fragment.append(button);
  });
  els.list.append(fragment);
}

function renderDetail() {
  const school = state.filtered.find((item) => item.id === state.selectedId);
  if (!school) {
    els.detail.innerHTML = `
      <div>
        <h2>Selecteer een school</h2>
        <p>Klik op een school in de lijst of op een punt in de kaart.</p>
      </div>
    `;
    return;
  }

  const ratioLabel = getSelectedRatioLabel();
  const selectedCount = getSelectedAdviceCount(school);
  const selectedCountLabel = state.includeHavoVwo ? "VWO of HAVO/VWO" : "VWO-advies";
  const website = school.website
    ? `<a href="${escapeAttr(school.website)}" target="_blank" rel="noreferrer">website</a>`
    : "";

  els.detail.innerHTML = `
    <div>
      <h2>${escapeHtml(school.name || "Onbekende school")}</h2>
      <p>${escapeHtml(compact([school.city, school.municipality, school.province]).join(" / "))}</p>
    </div>
    <div class="detail-grid">
      <div><strong>${formatRatio(school.ratio)}</strong><span>${ratioLabel}</span></div>
      <div><strong>${formatRange(selectedCount.min, selectedCount.max)}</strong><span>${selectedCountLabel}</span></div>
      <div><strong>${formatRange(school.advice?.totalMin, school.advice?.totalMax)}</strong><span>adviezen</span></div>
      <div><strong>${formatRange(school.pupils?.min, school.pupils?.max)}</strong><span>leerlingen</span></div>
    </div>
    ${renderAdviceHistory(school)}
    ${renderBackgroundDetail(school)}
    ${renderSatisfactionDetail(school)}
    ${renderOriginDetail(school)}
    <div class="address-line">
      ${escapeHtml(compact([school.address, school.postcode, school.city]).join(", "))}<br>
      BRIN ${escapeHtml(school.brin || "-")} / Vestiging ${escapeHtml(school.branch || "-")} / ${escapeHtml(school.denomination || "-")}
      ${school.distanceKm != null ? `<br>${school.distanceKm.toFixed(1)} km van het zoekcentrum` : ""}
    </div>
    <div class="source-line">
      Berekening: ${ratioLabel} ${formatRange(selectedCount.min, selectedCount.max)} / ${formatRange(school.advice?.totalMin, school.advice?.totalMax)} definitieve adviezen.
      ${school.advice?.redacted ? "DUO privacywaarden &lt;5 zijn als bereik verwerkt. " : ""}
      ${school.origin?.redacted ? "Herkomstwaarden onder 5 zijn als bereik verwerkt. " : ""}
      ${website}
    </div>
  `;
}

function renderOriginSummary(school) {
  if (!hasOrigin(school)) {
    return `
      <div class="origin-summary">
        <div class="origin-title">Herkomst postcode4</div>
        <div class="origin-empty">Geen DUO herkomstdata</div>
      </div>
    `;
  }

  const chips = (school.origin.top || []).slice(0, 3).map((item) => `
    <span>
      <strong>${escapeHtml(item.postcode4)}</strong>
      ${formatRatioRange(item.ratioMin, item.ratioMax)}
    </span>
  `).join("");

  return `
    <div class="origin-summary">
      <div class="origin-title">Herkomst postcode4 ${escapeHtml(String(school.origin.year || ""))}</div>
      <div class="origin-chips">${chips}</div>
    </div>
  `;
}

function renderBackgroundSummary(school) {
  if (!hasBackground(school)) {
    return "";
  }
  return `
    <div class="origin-summary background-summary">
      <div class="origin-title">Nationaliteit/achtergrond ${escapeHtml(String(school.background.year || ""))}</div>
      <div class="origin-chips">
        <span><strong>NNCA</strong>${formatRatioRange(school.background.nncaRatioMin, school.background.nncaRatioMax)}</span>
        <span><strong>${escapeHtml(school.background.measure || "DUO")}</strong>${formatRange(school.background.nncaMin, school.background.nncaMax)} leerlingen</span>
      </div>
    </div>
  `;
}

function renderAdviceHistory(school) {
  const history = (school.history?.advice || []).slice(-5);
  const label = state.includeHavoVwo ? "VWO + HAVO/VWO" : "VWO";
  if (!history.length) {
    return `
      <section class="trend-panel">
        <div class="trend-head">
          <h3>VWO-ratio laatste 5 jaar</h3>
          <span>--</span>
        </div>
        <p>Geen DUO-historie beschikbaar voor deze vestiging.</p>
      </section>
    `;
  }

  const rows = history.map((item) => {
    const min = state.includeHavoVwo ? item.vwoEligibleRatioMin : item.vwoRatioMin;
    const max = state.includeHavoVwo ? item.vwoEligibleRatioMax : item.vwoRatioMax;
    const width = clamp(midpoint(min, max) * 100, 0, 100);
    const countMin = state.includeHavoVwo ? item.vwoEligibleMin : item.vwoMin;
    const countMax = state.includeHavoVwo ? item.vwoEligibleMax : item.vwoMax;
    return `
      <div class="trend-row">
        <span>${escapeHtml(item.schoolYear || String(item.year || ""))}</span>
        <div class="trend-bar" aria-hidden="true"><i style="width:${width}%"></i></div>
        <strong>${formatRatioRange(min, max)}</strong>
        <em>${formatRange(countMin, countMax)} / ${formatRange(item.totalMin, item.totalMax)}</em>
      </div>
    `;
  }).join("");

  return `
    <section class="trend-panel">
      <div class="trend-head">
        <h3>VWO-ratio laatste 5 jaar</h3>
        <span>${escapeHtml(label)}</span>
      </div>
      <div class="trend-list">${rows}</div>
    </section>
  `;
}

function renderBackgroundDetail(school) {
  if (!hasBackground(school)) {
    return `
      <section class="trend-panel">
        <div class="trend-head">
          <h3>Nationaliteit/achtergrond leerlingen</h3>
          <span>DUO NNCA</span>
        </div>
        <p>Geen DUO-achtergronddata beschikbaar voor deze vestiging.</p>
      </section>
    `;
  }

  const history = (school.background.history || []).slice(-5);
  const rows = history.map((item) => {
    const width = clamp(midpoint(item.nncaRatioMin, item.nncaRatioMax) * 100, 0, 100);
    return `
      <div class="trend-row">
        <span>${escapeHtml(String(item.year || ""))}</span>
        <div class="trend-bar background-bar" aria-hidden="true"><i style="width:${width}%"></i></div>
        <strong>${formatRatioRange(item.nncaRatioMin, item.nncaRatioMax)}</strong>
        <em>${formatRange(item.nncaMin, item.nncaMax)} / ${formatRange(item.totalMin, item.totalMax)}</em>
      </div>
    `;
  }).join("");

  return `
    <section class="trend-panel">
      <div class="trend-head">
        <h3>Nationaliteit/achtergrond leerlingen</h3>
        <span>DUO ${escapeHtml(school.background.measure || "NNCA")} ${escapeHtml(String(school.background.year || ""))}</span>
      </div>
      <div class="trend-metric">
        <strong>${formatRatioRange(school.background.nncaRatioMin, school.background.nncaRatioMax)}</strong>
        <span>NNCA / niet-Nederlandse culturele achtergrond: ${formatRange(school.background.nncaMin, school.background.nncaMax)} leerlingen</span>
        <span>Overige achtergrond: ${formatRange(school.background.referenceMin, school.background.referenceMax)} leerlingen</span>
      </div>
      <div class="trend-list">${rows}</div>
    </section>
  `;
}

function renderSatisfactionDetail(school) {
  if (hasSatisfaction(school)) {
    return `
      <section class="trend-panel">
        <div class="trend-head">
          <h3>Tevredenheid</h3>
          <span>${escapeHtml(String(school.satisfaction.year || ""))}</span>
        </div>
        <div class="trend-metric">
          <strong>${formatSatisfaction(school.satisfaction)}</strong>
          <span>${escapeHtml(school.satisfaction.source || "")}</span>
        </div>
      </section>
    `;
  }

  return `
    <section class="trend-panel">
      <div class="trend-head">
        <h3>Tevredenheid</h3>
        <span>--</span>
      </div>
      <p>Geen openbare DUO tevredenheidsscore beschikbaar.</p>
    </section>
  `;
}

function renderOriginDetail(school) {
  if (!hasOrigin(school)) {
    return `
      <section class="origin-detail">
        <div class="origin-detail-head">
          <h3>Herkomst postcode4 leerlingen</h3>
          <span>--</span>
        </div>
        <p>Geen DUO herkomstdata voor deze vestiging.</p>
      </section>
    `;
  }

  const origin = school.origin;
  const bars = (origin.top || []).map((item) => {
    const width = clamp(midpoint(item.ratioMin, item.ratioMax) * 100, 0, 100);
    return `
      <div class="origin-row">
        <div>
          <strong>${escapeHtml(item.postcode4)}</strong>
          <span>${formatRange(item.min, item.max)} leerlingen</span>
        </div>
        <div class="origin-row-bar" aria-hidden="true"><span style="width:${width}%"></span></div>
        <em>${formatRatioRange(item.ratioMin, item.ratioMax)}</em>
      </div>
    `;
  }).join("");

  return `
    <section class="origin-detail">
      <div class="origin-detail-head">
        <h3>Herkomst postcode4 leerlingen</h3>
        <span>DUO ${escapeHtml(String(origin.year || ""))}</span>
      </div>
      <div class="origin-local">
        Eigen postcodegebied ${escapeHtml(origin.postcode4 || "--")}: ${formatRatioRange(origin.localRatioMin, origin.localRatioMax)}
        (${formatRange(origin.localMin, origin.localMax)} van ${formatRange(origin.totalMin, origin.totalMax)})
      </div>
      <div class="origin-bars">${bars}</div>
    </section>
  `;
}

function renderVisuals() {
  renderMap();
  renderDistribution();
}

function renderMap() {
  if (window.L && els.map) {
    renderLeafletMap();
    return;
  }
  renderFallbackMap();
}

function renderLeafletMap() {
  document.querySelector(".map-box")?.classList.remove("is-fallback");
  const schools = state.filtered.filter(hasLocation);
  const visibleSchools = state.center ? schools : schools.slice(0, 1800);

  if (!state.mapInstance) {
    state.mapInstance = L.map(els.map, {
      scrollWheelZoom: false,
      zoomControl: true,
      fadeAnimation: false
    });
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 19
    }).addTo(state.mapInstance);
    state.mapMarkers = L.layerGroup().addTo(state.mapInstance);
  }

  state.mapMarkers.clearLayers();
  if (state.mapRadius) {
    state.mapInstance.removeLayer(state.mapRadius);
    state.mapRadius = null;
  }

  const bounds = [];
  visibleSchools.forEach((school) => {
    const point = [Number(school.latitude), Number(school.longitude)];
    bounds.push(point);
  });
  if (state.center) {
    bounds.push([state.center.latitude, state.center.longitude]);
  }

  state.mapInstance.invalidateSize();
  if (bounds.length > 1) {
    state.mapInstance.fitBounds(bounds, { padding: [24, 24], maxZoom: state.center ? 14 : 8, animate: false });
  } else if (bounds.length === 1) {
    state.mapInstance.setView(bounds[0], state.center ? 13 : 8, { animate: false });
  } else {
    state.mapInstance.setView([52.16, 5.29], 7, { animate: false });
  }

  if (state.center) {
    state.mapRadius = L.circle([state.center.latitude, state.center.longitude], {
      radius: state.radiusKm * 1000,
      color: "#315f8c",
      weight: 2,
      fillColor: "#315f8c",
      fillOpacity: 0.08,
      opacity: 0.35
    }).addTo(state.mapInstance);
  }

  visibleSchools.forEach((school) => {
    const point = [Number(school.latitude), Number(school.longitude)];
    const marker = L.circleMarker(point, {
      radius: pointRadius(school, 1),
      color: school.id === state.selectedId ? "#17211d" : "#ffffff",
      weight: school.id === state.selectedId ? 3 : 1,
      fillColor: colorForRatio(school.ratio.mid),
      fillOpacity: school.id === state.selectedId ? 0.95 : 0.72
    });
    marker.bindTooltip(`${school.name || "School"}<br>${formatRatio(school.ratio)} VWO`, {
      direction: "top",
      opacity: 0.92
    });
    marker.on("click", () => selectSchool(school.id));
    marker.addTo(state.mapMarkers);
  });

  if (state.center) {
    L.circleMarker([state.center.latitude, state.center.longitude], {
      radius: 7,
      color: "#ffffff",
      weight: 3,
      fillColor: "#315f8c",
      fillOpacity: 1
    }).addTo(state.mapMarkers);
  }
}

function renderDistribution() {
  if (window.L && els.distributionMap) {
    renderDistributionMap();
    return;
  }
  renderScatter();
}

function renderDistributionMap() {
  document.querySelector(".scatter-box")?.classList.remove("is-fallback");
  const schools = state.filtered.filter((school) => hasLocation(school) && school.ratio.hasRatio);
  const visibleSchools = state.center ? schools : schools.slice(0, 1800);

  if (!state.distributionMapInstance) {
    state.distributionMapInstance = L.map(els.distributionMap, {
      scrollWheelZoom: false,
      zoomControl: true,
      fadeAnimation: false
    });
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 19
    }).addTo(state.distributionMapInstance);
    state.distributionMarkers = L.layerGroup().addTo(state.distributionMapInstance);
  }

  state.distributionMarkers.clearLayers();
  if (state.distributionRadius) {
    state.distributionMapInstance.removeLayer(state.distributionRadius);
    state.distributionRadius = null;
  }

  const bounds = [];
  visibleSchools.forEach((school) => bounds.push([Number(school.latitude), Number(school.longitude)]));
  if (state.center) {
    bounds.push([state.center.latitude, state.center.longitude]);
  }

  state.distributionMapInstance.invalidateSize();
  if (bounds.length > 1) {
    state.distributionMapInstance.fitBounds(bounds, { padding: [24, 24], maxZoom: state.center ? 14 : 8, animate: false });
  } else if (bounds.length === 1) {
    state.distributionMapInstance.setView(bounds[0], state.center ? 13 : 8, { animate: false });
  } else {
    state.distributionMapInstance.setView([52.16, 5.29], 7, { animate: false });
  }

  if (state.center) {
    state.distributionRadius = L.circle([state.center.latitude, state.center.longitude], {
      radius: state.radiusKm * 1000,
      color: "#315f8c",
      weight: 1,
      fillColor: "#315f8c",
      fillOpacity: 0.05,
      opacity: 0.25
    }).addTo(state.distributionMapInstance);
  }

  visibleSchools.forEach((school) => {
    const cohort = midpoint(school.advice?.totalMin, school.advice?.totalMax);
    const marker = L.circleMarker([Number(school.latitude), Number(school.longitude)], {
      radius: cohortRadius(cohort),
      color: school.id === state.selectedId ? "#17211d" : "#ffffff",
      weight: school.id === state.selectedId ? 3 : 1,
      fillColor: colorForRatio(school.ratio.mid),
      fillOpacity: school.id === state.selectedId ? 0.95 : 0.74
    });
    marker.bindTooltip(`${school.name || "School"}<br>${formatRatio(school.ratio)} VWO<br>${formatRange(school.advice?.totalMin, school.advice?.totalMax)} adviezen`, {
      direction: "top",
      opacity: 0.92
    });
    marker.on("click", () => selectSchool(school.id));
    marker.addTo(state.distributionMarkers);
  });
}

function renderFallbackMap() {
  document.querySelector(".map-box")?.classList.add("is-fallback");
  const canvas = setupCanvas(els.mapFallback, mapCtx);
  const ctx = mapCtx;
  const width = canvas.width;
  const height = canvas.height;
  const schools = state.filtered.filter(hasLocation).slice(0, 1200);

  ctx.clearRect(0, 0, width, height);
  drawNetherlandsBackdrop(ctx, width, height);

  if (state.center) {
    const centerPoint = project(state.center.longitude, state.center.latitude, width, height);
    const radiusPixels = radiusToPixels(state.radiusKm, state.center.latitude, width);
    ctx.beginPath();
    ctx.arc(centerPoint.x, centerPoint.y, radiusPixels, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(49, 95, 140, 0.08)";
    ctx.strokeStyle = "rgba(49, 95, 140, 0.35)";
    ctx.lineWidth = 2;
    ctx.fill();
    ctx.stroke();
  }

  schools.forEach((school) => {
    const point = project(Number(school.longitude), Number(school.latitude), width, height);
    school.__mapPoint = point;
    drawPoint(ctx, point.x, point.y, pointRadius(school), colorForRatio(school.ratio.mid), school.id === state.selectedId);
  });

  if (state.center) {
    const point = project(state.center.longitude, state.center.latitude, width, height);
    ctx.beginPath();
    ctx.arc(point.x, point.y, 7, 0, Math.PI * 2);
    ctx.fillStyle = "#315f8c";
    ctx.fill();
    ctx.lineWidth = 3;
    ctx.strokeStyle = "#ffffff";
    ctx.stroke();
  }
}

function renderScatter() {
  document.querySelector(".scatter-box")?.classList.add("is-fallback");
  const canvas = setupCanvas(els.scatter, scatterCtx);
  const ctx = scatterCtx;
  const width = canvas.width;
  const height = canvas.height;
  const schools = state.filtered.filter((school) => school.ratio.hasRatio).slice(0, 1200);
  const pad = { left: 42, right: 18, top: 20, bottom: 34 };
  const maxCohort = Math.max(10, ...schools.map((school) => midpoint(school.advice?.totalMin, school.advice?.totalMax)));

  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#f8fbf8";
  ctx.fillRect(0, 0, width, height);
  drawAxis(ctx, width, height, pad, maxCohort);

  schools.forEach((school) => {
    const cohort = midpoint(school.advice?.totalMin, school.advice?.totalMax);
    const x = pad.left + (Math.sqrt(cohort / maxCohort) * (width - pad.left - pad.right));
    const y = pad.top + ((1 - clamp(school.ratio.mid, 0, 1)) * (height - pad.top - pad.bottom));
    school.__scatterPoint = { x, y };
    drawPoint(ctx, x, y, pointRadius(school), colorForRatio(school.ratio.mid), school.id === state.selectedId);
  });
}

function drawNetherlandsBackdrop(ctx, width, height) {
  const outline = [
    [3.35, 51.35], [3.75, 51.22], [4.14, 51.45], [4.75, 51.43],
    [5.10, 51.73], [5.88, 51.75], [6.20, 52.08], [6.95, 52.16],
    [7.05, 52.54], [6.72, 52.97], [6.42, 53.23], [5.85, 53.42],
    [5.15, 53.38], [4.78, 52.98], [4.62, 52.55], [4.12, 52.36],
    [3.82, 51.95], [3.35, 51.35]
  ].map(([lon, lat]) => project(lon, lat, width, height));

  ctx.beginPath();
  outline.forEach((point, index) => {
    if (index === 0) ctx.moveTo(point.x, point.y);
    else ctx.lineTo(point.x, point.y);
  });
  ctx.closePath();
  ctx.fillStyle = "#edf4ef";
  ctx.fill();
  ctx.strokeStyle = "#d2ded7";
  ctx.lineWidth = 2;
  ctx.stroke();

  ctx.strokeStyle = "rgba(102, 116, 110, 0.13)";
  ctx.lineWidth = 1;
  for (let i = 1; i < 5; i += 1) {
    const x = (width / 5) * i;
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, height);
    ctx.stroke();
  }
  for (let i = 1; i < 4; i += 1) {
    const y = (height / 4) * i;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(width, y);
    ctx.stroke();
  }
}

function drawAxis(ctx, width, height, pad, maxCohort) {
  ctx.strokeStyle = "#d2ded7";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(pad.left, pad.top);
  ctx.lineTo(pad.left, height - pad.bottom);
  ctx.lineTo(width - pad.right, height - pad.bottom);
  ctx.stroke();

  ctx.fillStyle = "#66746e";
  ctx.font = `${12 * devicePixelRatio}px Inter, Segoe UI, sans-serif`;
  ctx.textAlign = "left";
  ctx.fillText("100%", 8, pad.top + 8);
  ctx.fillText("0%", 16, height - pad.bottom + 4);
  ctx.textAlign = "right";
  ctx.fillText(`${Math.round(maxCohort)} adviezen`, width - pad.right, height - 10);
}

function drawPoint(ctx, x, y, radius, color, selected) {
  ctx.beginPath();
  ctx.arc(x, y, selected ? radius + 4 : radius, 0, Math.PI * 2);
  ctx.fillStyle = color;
  ctx.globalAlpha = selected ? 1 : 0.72;
  ctx.fill();
  ctx.globalAlpha = 1;
  ctx.lineWidth = selected ? 3 : 1;
  ctx.strokeStyle = selected ? "#17211d" : "rgba(255, 255, 255, 0.78)";
  ctx.stroke();
}

function pickSchoolFromCanvas(event, canvas, scatter = false) {
  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  const x = (event.clientX - rect.left) * scaleX;
  const y = (event.clientY - rect.top) * scaleY;
  let winner = null;
  let best = Infinity;

  state.filtered.forEach((school) => {
    const point = scatter ? school.__scatterPoint : school.__mapPoint;
    if (!point) return;
    const dist = Math.hypot(point.x - x, point.y - y);
    if (dist < best && dist < 18 * devicePixelRatio) {
      winner = school;
      best = dist;
    }
  });

  return winner;
}

function selectSchool(id) {
  state.selectedId = id;
  render();
}

function getRatioMetric(school) {
  const advice = school.advice || {};
  const numeratorMin = state.includeHavoVwo ? advice.vwoEligibleMin : advice.vwoMin;
  const numeratorMax = state.includeHavoVwo ? advice.vwoEligibleMax : advice.vwoMax;
  const totalMin = Number(advice.totalMin);
  const totalMax = Number(advice.totalMax);

  if (!Number.isFinite(totalMin) || !Number.isFinite(totalMax) || totalMax <= 0) {
    return { min: 0, max: 0, mid: 0, hasRatio: false, redacted: false };
  }

  const bounds = ratioBounds(numeratorMin, numeratorMax, totalMin, totalMax);
  return {
    min: bounds.min,
    max: bounds.max,
    mid: (bounds.min + bounds.max) / 2,
    hasRatio: true,
    redacted: Boolean(advice.redacted || bounds.min !== bounds.max)
  };
}

function getSelectedRatioLabel() {
  return state.includeHavoVwo ? "VWO + HAVO/VWO" : "VWO";
}

function getSelectedAdviceCount(school) {
  const advice = school.advice || {};
  return state.includeHavoVwo
    ? { min: advice.vwoEligibleMin, max: advice.vwoEligibleMax }
    : { min: advice.vwoMin, max: advice.vwoMax };
}

function getRatioQualityLabel(school) {
  if (!school.ratio?.hasRatio) return "";
  const rangeWidth = Math.abs(Number(school.ratio.max || 0) - Number(school.ratio.min || 0));
  const cohortMax = Number(school.advice?.totalMax || 0);
  if (rangeWidth >= 0.2 || (cohortMax > 0 && cohortMax <= 20)) return "breed DUO-bereik";
  if (school.ratio.redacted) return "DUO-bereik";
  return "";
}

function compareRatioRank(a, b) {
  const minDiff = Number(b.ratio?.min || 0) - Number(a.ratio?.min || 0);
  if (Math.abs(minDiff) > 0.0001) return minDiff;
  return Number(b.ratio?.mid || 0) - Number(a.ratio?.mid || 0);
}

function setupCanvas(canvas, ctx) {
  const rect = canvas.getBoundingClientRect();
  const ratio = window.devicePixelRatio || 1;
  const width = Math.max(1, Math.round(rect.width * ratio));
  const height = Math.max(1, Math.round(rect.height * ratio));
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  return canvas;
}

function project(lon, lat, width, height) {
  const x = ((lon - NL_BOUNDS.minLon) / (NL_BOUNDS.maxLon - NL_BOUNDS.minLon)) * width;
  const y = (1 - ((lat - NL_BOUNDS.minLat) / (NL_BOUNDS.maxLat - NL_BOUNDS.minLat))) * height;
  return { x, y };
}

function radiusToPixels(km, lat, width) {
  const kmPerDegreeLon = 111.32 * Math.cos((lat * Math.PI) / 180);
  const degrees = km / Math.max(kmPerDegreeLon, 1);
  return (degrees / (NL_BOUNDS.maxLon - NL_BOUNDS.minLon)) * width;
}

function pointRadius(school, pixelRatio = window.devicePixelRatio || 1) {
  const pupils = midpoint(school.pupils?.min, school.pupils?.max);
  return (3.5 + Math.min(5, Math.sqrt(Math.max(pupils, 0)) / 10)) * pixelRatio;
}

function cohortRadius(cohort) {
  return 4 + Math.min(9, Math.sqrt(Math.max(Number(cohort) || 0, 0)) / 2.1);
}

function colorForRatio(value) {
  const t = clamp(value, 0, 0.75) / 0.75;
  const low = [212, 111, 53];
  const high = [31, 143, 131];
  const rgb = low.map((channel, index) => Math.round(channel + ((high[index] - channel) * t)));
  return `rgb(${rgb.join(",")})`;
}

function distanceKm(lat1, lon1, lat2, lon2) {
  const earth = 6371;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a = Math.sin(dLat / 2) ** 2
    + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  return earth * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function toRad(deg) {
  return (deg * Math.PI) / 180;
}

function hasLocation(school) {
  if (school.latitude == null || school.longitude == null) return false;
  if (school.latitude === "" || school.longitude === "") return false;
  return Number.isFinite(Number(school.latitude)) && Number.isFinite(Number(school.longitude));
}

function hasOrigin(school) {
  const totalMax = Number(school.origin?.totalMax);
  return Number.isFinite(totalMax) && totalMax > 0 && Array.isArray(school.origin?.top);
}

function hasAdviceHistory(school) {
  return Array.isArray(school.history?.advice) && school.history.advice.length > 0;
}

function hasBackground(school) {
  const totalMax = Number(school.background?.totalMax);
  return Number.isFinite(totalMax) && totalMax > 0;
}

function hasSatisfaction(school) {
  if (school.satisfaction?.score == null || school.satisfaction?.score === "") return false;
  return Number.isFinite(Number(school.satisfaction.score));
}

function hasSelectOption(select, value) {
  return Array.from(select.options).some((option) => option.value === value);
}

function normalize(value) {
  return String(value || "")
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function normalizePostcode(value) {
  return String(value || "").replace(/\s+/g, "").toUpperCase();
}

function compact(values) {
  return values.filter((value) => value != null && String(value).trim() !== "");
}

function midpoint(min, max) {
  const a = Number(min);
  const b = Number(max);
  if (!Number.isFinite(a) && !Number.isFinite(b)) return 0;
  if (!Number.isFinite(a)) return b;
  if (!Number.isFinite(b)) return a;
  return (a + b) / 2;
}

function nullableNumber(value) {
  return value == null || !Number.isFinite(Number(value)) ? Number.POSITIVE_INFINITY : Number(value);
}

function nullableNumberDescending(value) {
  return value == null || !Number.isFinite(Number(value)) ? Number.NEGATIVE_INFINITY : Number(value);
}

function medianOf(values) {
  if (!values.length) return NaN;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

function formatRatio(ratio) {
  if (!ratio?.hasRatio) return "--";
  if (Math.abs(ratio.max - ratio.min) < 0.005) return formatPercent(ratio.mid);
  return `${formatPercent(ratio.min)}-${formatPercent(ratio.max)}`;
}

function formatPercent(value) {
  return `${Math.round(value * 100)}%`;
}

function formatSatisfaction(value) {
  if (value?.score == null || value?.score === "") return "--";
  const score = Number(value?.score);
  if (!Number.isFinite(score)) return "--";
  return score.toLocaleString("nl-NL", { maximumFractionDigits: 1 });
}

function ratioBounds(numeratorMin, numeratorMax, totalMin, totalMax) {
  const minNumerator = Number(numeratorMin || 0);
  const maxNumerator = Number(numeratorMax || 0);
  const minTotal = Number(totalMin || 0);
  const maxTotal = Number(totalMax || 0);
  const otherMax = Math.max(0, maxTotal - maxNumerator);
  const otherMin = Math.max(0, minTotal - minNumerator);
  const minDenominator = minNumerator + otherMax;
  const maxDenominator = maxNumerator + otherMin;
  return {
    min: minDenominator > 0 ? clamp(minNumerator / minDenominator, 0, 1) : 0,
    max: maxDenominator > 0 ? clamp(maxNumerator / maxDenominator, 0, 1) : 0
  };
}

function formatRatioRange(min, max) {
  const a = Number(min);
  const b = Number(max);
  if (!Number.isFinite(a) || !Number.isFinite(b)) return "--";
  if (Math.abs(a - b) < 0.005) return formatPercent((a + b) / 2);
  return `${formatPercent(a)}-${formatPercent(b)}`;
}

function formatRange(min, max) {
  const a = Number(min);
  const b = Number(max);
  if (!Number.isFinite(a) && !Number.isFinite(b)) return "--";
  if (a === b) return a.toLocaleString("nl-NL");
  return `${a.toLocaleString("nl-NL")}-${b.toLocaleString("nl-NL")}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value).replace(/`/g, "&#096;");
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function debounce(fn, wait) {
  let timer = null;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), wait);
  };
}
