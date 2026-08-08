const API_BASE_URL = import.meta.env.VITE_API_BASE_URL
const API_KEY = import.meta.env.VITE_API_KEY

/**
 * Fetch JSON from the CosmiDex API with the required X-API-Key header.
 *
 * @param path - API path (including query string), relative to API_BASE_URL.
 * @returns A promise resolving to the parsed JSON response body.
 * @throws {Error} If the response status is not ok.
 */
export function apiFetch(path, options = {}) {
    const method = options.method || 'GET'
    const body = options.body

    return fetch(`${API_BASE_URL}${path}`, {
        method: method,
        headers: {
            'X-API-Key': API_KEY,
            'Content-Type': 'application/json',
        },
        body: body ? JSON.stringify(body) : undefined,
    }).then(res => {
        if (!res.ok) {
            throw new Error(`Request failed (${res.status})`)
        }
        return res.json()
    })
}
