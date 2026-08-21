import axios from "axios";

// all axios functions live here and imported into other files as needed

const baseURL = 'locahost:'

// Extremely basic structure, will need headers for auth
export async function login(username, password) {
  loading.value = true
  //place holder untill backend route operational
  const response = await axios.post('${baseURL}:8000/api/login', {
    username: username.value, // has vue dependency might need to be changed
    password: password.value,
  })

  console.log('logged in', response.data)
}
