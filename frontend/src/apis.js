import axios from "axios";

// all axios functions live here and imported into other files as needed

const api = axios.create({
  baseURL: "http://localhost:8000/api",
  withCredentials: true,
  xsrfCookieName: "csrftoken",
  xsrfHeaderName: "X-CSRFToken",
})

// Extremely basic structure, will need headers for auth
export async function login(username, password) {
  //place holder untill backend route operational
  const response = await api.post("/auth/login/", {
    username: username,
    password: password
  })

  return response.data

  console.log('logged in', response.data)
}

export async function fetchCsrfCookie() {
  await api.get("/auth/csrf/")
}
