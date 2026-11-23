async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(path, {
      ...options,
      headers: { Accept: "application/json", ...options.headers },
    });
  } catch {
    throw new Error("Cannot reach the server.");
  }

  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const apiError = body?.error ?? {};
    const error = new Error(apiError.message ?? "Something went wrong.");
    error.code = apiError.code;
    error.details = apiError.details ?? {};
    throw error;
  }
  return body;
}

function sendJson(method, path, data) {
  return request(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export function listMovies() {
  return request("/api/movies");
}

export function createMovie(data) {
  return sendJson("POST", "/api/movies", data);
}

export function updateMovie(id, data) {
  return sendJson("PATCH", `/api/movies/${id}`, data);
}

export function getRewatchOrder(id) {
  return request(`/api/movies/${id}/rewatch-order`);
}

export function listCinemas() {
  return request("/api/cinemas");
}

export function createCinema(data) {
  return sendJson("POST", "/api/cinemas", data);
}

export function getBookingQuote(id, groupSize) {
  const query = new URLSearchParams({ groupSize });
  return request(`/api/cinemas/${id}/booking?${query}`);
}
