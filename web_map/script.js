let map;
let service;

// Emoji symbols based on icon_type
const SYMBOLS = {
    "ramen": "🍜",
    "sushi": "🍣",
    "cafe": "☕",
    "izakaya": "🍶",
    "default": "🍱"
};

async function initMap() {
    try {
        const response = await fetch('data/restaurants.json');
        const restaurants = await response.json();

        // Standard clean Google Maps layout (no styles = modern default)
        map = new google.maps.Map(document.getElementById("map"), {
            center: { lat: 35.6812, lng: 139.7671 },
            zoom: 14,
            disableDefaultUI: false, // Restore native tools
            zoomControl: true,
            mapTypeControl: false,
            streetViewControl: true,
            fullscreenControl: false
        });

        service = new google.maps.places.PlacesService(map);

        restaurants.forEach(res => {
            if (!res.lat || !res.lng) return;

            const markerElement = document.createElement("div");
            markerElement.className = "category-marker";
            markerElement.innerHTML = SYMBOLS[res.icon_type] || SYMBOLS["default"];

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
        });

    } catch (error) {
        console.error('Error loading restaurant data:', error);
    }
}

function showDetails(res) {
    const panel = document.getElementById("info-panel");

    // Initial content with Notion data
    panel.innerHTML = `
        <div class="card-header" id="photo-placeholder">
            <div style="height:200px; background:#eee; display:flex; align-items:center; justify-content:center; color:#999;">이미지 불러오는 중...</div>
        </div>
        <div class="card-body">
            <div class="restaurant-name">${res.name}</div>
            <div class="rating-row">
                <span class="rating-badge rating-tabelog">Tabelog ${res.tabelog_rating || '?'}</span>
                <span class="rating-badge rating-google">Google ${res.google_rating || '?'}</span>
            </div>
            <p class="summary">${res.summary}</p>
            <div class="tag-list">
                ${res.tags.map(t => `<span class="tag-item">#${t}</span>`).join('')}
            </div>
            <div class="info-row">📍 ${res.address}</div>
            <div class="info-row">🚉 ${res.station || ''}</div>
        </div>
        <div class="action-row" id="action-placeholder">
             <a href="${res.google_url}" target="_blank" class="btn-primary">Google Maps에서 열기</a>
        </div>
    `;

    // Enrich with native Google Place data
    if (res.place_id) {
        service.getDetails({
            placeId: res.place_id,
            fields: ['opening_hours', 'photos', 'url', 'rating', 'user_ratings_total']
        }, (place, status) => {
            if (status === google.maps.places.PlacesServiceStatus.OK) {
                // Update photo
                if (place.photos && place.photos.length > 0) {
                    const photoUrl = place.photos[0].getUrl();
                    document.getElementById("photo-placeholder").innerHTML = `<img class="card-photo" src="${photoUrl}" />`;
                }

                // Add opening hours if available
                if (place.opening_hours) {
                    const hoursDiv = document.createElement("div");
                    hoursDiv.className = "info-row";
                    hoursDiv.innerHTML = `🕒 ${place.opening_hours.weekday_text[new Date().getDay() % 7] || '영업시간 확인 필요'}`;
                    panel.querySelector(".card-body").appendChild(hoursDiv);
                }
            }
        });
    }
}

window.initMap = initMap;
