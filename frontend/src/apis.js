import axios from "axios";
import Cookies from "js-cookie";

const api = axios.create({
  baseURL: "http://localhost:8000/api",
  withCredentials: true,
});

export async function fetchCsrfCookie() {
  await api.get("/auth/csrf/");
}

export async function login(username, password) {

  const csrfToken = Cookies.get("csrftoken");
  const response = await api.post(
    "/auth/login/",
    {
      username,
      password,
    },
    {
      headers: {
        "X-CSRFToken": csrfToken,
      },
    }
  );

  return response.data;
}