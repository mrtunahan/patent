// API için tek yapılandırma noktası. Tüm istekler bu taban adresini kullanır.
// BASE_URL, VITE_BASE_PATH'ten gelir ve her zaman "/" ile biter ("/" veya "/patent/").
export const API_BASE = `${import.meta.env.BASE_URL}api`
