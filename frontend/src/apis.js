import axios from "axios"
export const MAX_ATTEMPTS = 3
export const TIMEOUT_ERROR = "ETIMEDOUT"

const api = axios.create({
  baseURL: "http://localhost:8000/api",
  withCredentials: true,
  withXSRFToken: true,
  xsrfCookieName: "csrftoken",
  xsrfHeaderName: "X-CSRFToken",
  timeout: 5000,
  transitional: {
        clarifyTimeoutError: true,
    }
});

// Helper function to pause execution for 'ms' milliseconds
function sleep(ms) {
  return new Promise(function (resolve) {
    setTimeout(resolve, ms);
  });
}

// Wrapper function to retry an axios request up to 'maxRetries' times
// Follows exponential backoff principle
// NOTE: Retrying GET requests is recommended, but be careful when retrying 
// POST requests 

// IMPORTANT: Should wrap read-only (GET) calls broadly, be optional but reasonable on idempotent updates (PATCH)
export async function withRetry(maxRetries, axiosFunction, ...args) {
  // Set default value manually if not provided
  if (maxRetries === undefined || maxRetries === null)
    maxRetries = MAX_ATTEMPTS

  for (let x = 1; x <= maxRetries; x++) {
    try {
      return await axiosFunction(...args);
    } catch (error) {
      var isTimeout = error.code === TIMEOUT_ERROR

      if (isTimeout && x < maxRetries) {
        // jitter of upto 500ms to prevent multiple clients sending requests at same time
        const jitter = Math.random() * 500
        const dropOffTime = 100 * Math.pow(2, x - 1) + jitter
        await sleep(dropOffTime)
        console.log("Response Timeout. Retrying")
        continue
      }
      // different error
      throw error
    }
  }
}

// fetch Crsf token and store it as a cookie
// for future requests
export async function fetchCsrfCookie() {
  await api.get("/auth/csrf/")
}

export async function login(email, password) {
  const response = await api.post(
    "/auth/login/",
    {
      email,
      password,
    }
  )
  return response.data;

}

export async function logout() {
  const response = await api.post(
    "/auth/logout/"
  )
  return response.data
}

export async function fetchMe() {
  const response = await api.get(
    "/auth/me/",
  )
  return response.data
}

/* ---- staff ---- */

export async function createStaffAccount(payload){
  const response = await api.post(
      "/auth/staff/", 
      payload
    )
  return response.data
}

export async function listStaff() {
  const response = await api.get("/auth/staff/list/")
  return response.data
}

export async function deactivateStaff(id) {
  const response = await api.post(`/auth/staff/${id}/deactivate/`)
  return response.data
}

/* ---- branches ---- */

// params: { search, no_manager } — both optional, both handled server side.
// Returns id/name/region plus manager_name and participant_count, so the same
// call serves both the Branch table and the branch pickers on the staff forms.
export async function listBranches(params = {}) {
  const response = await api.get("/branches/", { params })
  return response.data
}

export async function createBranch(payload) {
  const response = await api.post("/branches/", payload)
  return response.data
}

export async function getBranch(id) {
  const response = await api.get(`/branches/${id}/`)
  return response.data
}

export async function updateBranch(id, payload) {
  const response = await api.patch(`/branches/${id}/`, payload)
  return response.data
}

/* ---- participants ---- */

// params: { branch, is_active, search } — all optional.
export async function listParticipants(params = {}) {
  const response = await api.get("/participants/", { params })
  return response.data
}

export async function getParticipant(id) {
  const response = await api.get(`/participants/${id}/`)
  return response.data
}

export async function createParticipant(payload) {
  const response = await api.post("/participants/", payload)
  return response.data
}

export async function getParticipantAttendance(id) {
  const response = await api.get(`/participants/${id}/attendance/`)
  return response.data
}

// Fetch through the authenticated API; no permanent document URL is exposed.
export async function downloadGpDocument(id) {
  const response = await api.get(`/participants/${id}/gp-document/`, { responseType: 'blob' })
  return response.data
}

export async function updateParticipant(id, payload) {
  const response = await api.patch(`/participants/${id}/`, payload)
  return response.data
}

export async function deactivateParticipant(id) {
  const response = await api.post(`/participants/${id}/deactivate/`)
  return response.data
}

export async function deleteBranch(id) {
  const response = await api.delete(`/branches/${id}/`)
  return response.data
}

// Assigning also grants the Branch Manager role, and moves the person off any
// branch they were on. The response reports both so the UI can say what happened.
export async function assignBranchManager(branchId, userId) {
  const response = await api.post(`/branches/${branchId}/managers/`, { user_id: userId })
  return response.data
}

export async function removeBranchManager(branchId, userId) {
  const response = await api.delete(`/branches/${branchId}/managers/${userId}/`)
  return response.data
}

export async function assignBranchInstructor(branchId, userId) {
  const response = await api.post(`/branches/${branchId}/instructors/`, { user_id: userId })
  return response.data
}

export async function removeBranchInstructor(branchId, userId) {
  const response = await api.delete(`/branches/${branchId}/instructors/${userId}/`)
  return response.data
}

/* ---- sessions ---- */

export async function listSessions(params = {}) {
  const response = await api.get("/sessions/", { params })
  return response.data
}

export async function getSession(id) {
  const response = await api.get(`/sessions/${id}/`)
  return response.data
}

export async function createSession(payload) {
  const response = await api.post("/sessions/", payload)
  return response.data
}

export async function updateAttendance(sessionId, attendanceId, changes) {
  const response = await api.patch(`/sessions/${sessionId}/attendance/${attendanceId}/`, changes)
  return response.data
}

export async function deleteSession(id) {
  await api.delete(`/sessions/${id}/`)
}
