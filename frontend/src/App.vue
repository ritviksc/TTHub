<script setup>
</script>

<template>
  <nav>
    <!--TODO: Needs to be conditional based on user state-->
    <RouterLink to="/">Home</RouterLink>
    <RouterLink to="/about">About Us</RouterLink>
    <RouterLink to="/contact">Contact Us</RouterLink>
    <RouterLink to="/login">Login</RouterLink>
  </nav>
  <main>
    <RouterView />
  </main>
</template>

<style scoped></style>
