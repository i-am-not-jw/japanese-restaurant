let map;
let service;
let markers = []; // Track all markers for easy clearing

// Emoji symbols based on icon_type (Universal Japanese Style)
const SYMBOLS = {
    "restaurant": "🥢",
    "cafe": "🍵",
    "izakaya": "🏮",
    "sakura": "🌸",
    "castle": "🏯",
    "shrine": "⛩️",
    "default": "🍱"
};

// Tag category color mapping (Notion Standard)
const TAG_COLORS = {
    "badge": { bg: "#FDECC8", color: "#D9730D" },
    "cuisine": { bg: "#D3E5EF", color: "#097EB0" },
    "location": { bg: "#EFE0DE", color: "#976D57" },
    "payment": { bg: "#EDF3EC", color: "#448361" },
    "default": { bg: "#EBECED", color: "#91918E" }
};

// Filter Configuration
const REGION_HIERARCHY = {
    "도쿄": ["미나토구", "시부야구", "중앙구", "신주쿠", "신바시", "가마타"],
    "오사카": ["미나토구"],
    "교토": ["기온", "시조"],
    "홋카이도": ["삿포로", "하코다테"],
    "구마모토": ["주오구"],
    "아이치": ["나고야"],
    "후쿠오카": ["텐진"],
    "가가와": ["다카마쓰"],
    "이시카와": ["가나자와"],
    "치바": ["후나바시"],
    "가고시마": ["아마미"]
};

const CUISINE_GROUPS = [
    { label: "---면류---", items: ["라멘", "우동", "소바", "츠케멘"] },
    { label: "---일식---", items: ["스시", "돈카츠", "텐동", "카이센동", "장어", "나베", "야키토리"] },
    { label: "---고기---", items: ["야키니쿠", "스테이크"] },
    { label: "---술/바---", items: ["이자카야", "다이닝 바", "바(Bar)"] },
    { label: "---기타---", items: ["양식", "이탈리안", "프렌치", "카레", "햄버거", "해산물"] },
    { label: "---디저트---", items: ["카페", "디저트", "베이커리"] }
];

let activeRegion = null;
let activeSubRegion = null;
let activeCuisine = null;

function getTagStyle(tag) {
    if (tag.includes("맛집") || tag.includes("인증") || tag.includes("레전드") || tag.includes("💡") || tag.includes("🏆")) return TAG_COLORS["badge"];
    const cuisineKeywords = ["라멘", "스시", "초밥", "야키니쿠", "스테이크", "카페", "이자카야", "이탈리안", "프렌치", "해산물", "나베", "야키토리", "꼬치", "우동", "소바", "텐동", "카레", "버거", "다이닝 바", "바(Bar)"];
    if (cuisineKeywords.some(k => tag.includes(k))) return TAG_COLORS["cuisine"];
    const locationKeywords = ["구", "시", "도쿄", "오사카", "교토", "나고야", "삿포로", "후쿠오카", "구마모토", "치바", "가마쿠라", "요코하마", "에히메", "가가와", "고치", "도쿠시마", "신바시", "미나토구", "중앙구", "시부야", "신주쿠", "다카마쓰", "하코다테", "가나자와", "이시카와", "노토", "아오모리", "기후", "미에", "나가노", "시즈오카", "와카야마", "톳토리", "시마네", "오카야마", "히로시마", "야마구치", "후쿠이", "토야마", "나가사키", "오이타", "미야자키", "가고시마", "오키나와", "홋카이도", "센다이", "나라", "아이치"];
    if (locationKeywords.some(k => tag.includes(k))) return TAG_COLORS["location"];
    if (tag.includes("카드") || tag.includes("결제") || tag.includes("예약") || tag.includes("현금")) return TAG_COLORS["payment"];
    return TAG_COLORS["default"];
}

async function initMap() {
    try {
        const JAPAN_BOUNDS = { north: 45.6, south: 24.3, east: 154.0, west: 122.9 };
        map = new google.maps.Map(document.getElementById("map"), {
            center: { lat: 36.2048, lng: 138.2529 },
            zoom: 6,
            mapId: "DEMO_MAP_ID",
            disableDefaultUI: true,
            restriction: { latLngBounds: JAPAN_BOUNDS, strictBounds: false },
        });

        service = new google.maps.places.PlacesService(map);

        setupFilters();
        renderMarkers();
    } catch (error) {
        console.error('Error loading map:', error);
    }
}

function setupFilters() {
    const regionSelect = document.getElementById("region-select");
    const cuisineSelect = document.getElementById("cuisine-select");

    // Populate Region Dropdown
    Object.keys(REGION_HIERARCHY).forEach(reg => {
        const opt = document.createElement("option");
        opt.value = reg;
        opt.textContent = reg;
        regionSelect.appendChild(opt);
    });

    // Populate Cuisine Dropdown with optgroups
    CUISINE_GROUPS.forEach(group => {
        const optgroup = document.createElement("optgroup");
        optgroup.label = group.label.replace(/-/g, ''); // Clean labels

        group.items.forEach(item => {
            const opt = document.createElement("option");
            opt.value = item;
            opt.textContent = item;
            optgroup.appendChild(opt);
        });
        cuisineSelect.appendChild(optgroup);
    });

    // Event Listeners
    regionSelect.onchange = (e) => {
        activeRegion = e.target.value;
        activeSubRegion = null;
        updateSubRegionDropdown();
        renderMarkers();
    };

    cuisineSelect.onchange = (e) => {
        activeCuisine = e.target.value;
        renderMarkers();
    };
}

function updateSubRegionDropdown() {
    const subSelect = document.getElementById("sub-region-select");
    if (!activeRegion || !REGION_HIERARCHY[activeRegion]) {
        subSelect.style.display = "none";
        subSelect.value = "";
        return;
    }

    subSelect.innerHTML = '<option value="">세부 지역 선택 (전체)</option>';
    REGION_HIERARCHY[activeRegion].forEach(sub => {
        const opt = document.createElement("option");
        opt.value = sub;
        opt.textContent = sub;
        subSelect.appendChild(opt);
    });

    subSelect.style.display = "block";
    subSelect.onchange = (e) => {
        activeSubRegion = e.target.value;
        renderMarkers();
    };
}

function renderMarkers() {
    // Clear existing markers
    markers.forEach(m => m.setMap(null));
    markers = [];

    const data = window.RESTAURANT_DATA || [];

    data.forEach(res => {
        // Filter Logic
        if (activeRegion && !res.region.includes(activeRegion)) return;
        if (activeSubRegion && !res.tags.some(t => t.includes(activeSubRegion)) && !res.address.includes(activeSubRegion)) return;
        if (activeCuisine && !res.tags.some(t => t.includes(activeCuisine)) && !res.summary.includes(activeCuisine)) return;

        const markerElement = document.createElement("div");
        markerElement.className = "category-marker";
        // Simple icon determination for now (reuse SYMBOLS)
        let icon = "🥢";
        if (res.tags.includes("이자카야")) icon = "🏮";
        if (res.tags.includes("카페")) icon = "🍵";

        markerElement.innerHTML = `<div class="category-marker-inner">${icon}</div>`;

        const marker = new google.maps.marker.AdvancedMarkerElement({
            position: { lat: parseFloat(res.lat), lng: parseFloat(res.lng) },
            map: map,
            title: res.name,
            content: markerElement
        });

        marker.addListener("click", () => {
            showDetails(res);
            map.panTo(marker.position);
        });

        markers.push(marker);
    });
}

function showDetails(res) {
    const panel = document.getElementById("info-panel");
    const photoUrl = res.thumbnail || "";
    const photoHtml = photoUrl
        ? `<img class="card-photo" src="${photoUrl}" />`
        : `<div class="card-photo-placeholder">이미지 없음</div>`;

    panel.innerHTML = `
        <div class="card-header">${photoHtml}</div>
        <div class="card-body">
            <div class="restaurant-name">${res.name}</div>
            <div class="rating-row">
                <span class="rating-badge rating-tabelog">Tabelog ${res.tabelog_rating || '?'}</span>
                <span class="rating-badge rating-google">Google ${res.google_rating || '?'}</span>
            </div>
            <p class="summary">${res.summary}</p>
            <div class="tag-list">
                ${res.tags.map(t => {
        const style = getTagStyle(t);
        return `<span class="tag-item" style="background:${style.bg}; color:${style.color};">#${t}</span>`;
    }).join('')}
            </div>
            <div class="info-row">📍 ${res.address}</div>
            <div class="info-row">🚉 ${res.station || ''}</div>
        </div>
        <div class="info-footer">
            <div class="date-label"><span>최초 수집</span> <span>${res.created_at || '-'}</span></div>
            <div class="date-label"><span>최종 동기화</span> <span>${res.updated_at || '-'}</span></div>
        </div>
        <div class="action-row">
             <a href="${res.google_url}" target="_blank" class="btn-primary">Google Maps에서 열기</a>
        </div>
    `;
    panel.classList.add("active");
}

window.initMap = initMap;
