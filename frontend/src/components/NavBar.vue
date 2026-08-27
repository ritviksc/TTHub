<script setup>
import { RouterLink } from 'vue-router'
</script>

<template>
  <nav class="navbar">
    <!-- Brand -->
    <RouterLink to="/" class="navbar-brand">
      Taurite Tū
    </RouterLink>

    <!-- Navigation -->
    <div class="navbar-links">
      <RouterLink to="/">Home</RouterLink>

      <RouterLink to="/about">About Us</RouterLink>

      <RouterLink to="/contact">Contact Us</RouterLink>

      <RouterLink to="/login" class="navbar-login">
        Login
      </RouterLink>
    </div>
  </nav>
</template>

<style scoped>
/* =========================
   NAVBAR
========================= */

.navbar {
  width: 100%;
  height: 64px;

  display: flex;
  align-items: center;
  justify-content: space-between;

  padding: 0 32px;

  background: #151515;
  border-bottom: 1px solid #2a2a2a;

  font-family: 'Inter', sans-serif;

  box-sizing: border-box;
}

/* =========================
   BRAND
========================= */

.navbar-brand {
  color: #00a9ac;

  font-family: 'Playfair Display', serif;

  font-size: 1.45rem;
  font-weight: 700;

  text-decoration: none;

  letter-spacing: 0.3px;

  transition: opacity 0.2s ease;
}

.navbar-brand:hover {
  opacity: 0.85;
}

/* =========================
   NAVIGATION LINKS
========================= */

.navbar-links {
  display: flex;
  align-items: center;

  gap: 8px;
}

.navbar-links a {
  position: relative;

  color: #c9c9c9;

  text-decoration: none;

  font-size: 0.95rem;
  font-weight: 500;

  padding: 9px 14px;

  border-radius: 7px;

  transition:
    color 0.2s ease,
    background 0.2s ease;
}

/* Hover */

.navbar-links a:hover {
  color: #ffffff;
  background: #222222;
}

/* =========================
   ACTIVE LINK
========================= */

.navbar-links a.router-link-active {
  color: #00a9ac;

  background: rgba(0, 169, 172, 0.08);
}

.navbar-links a.router-link-active::after {
  content: '';

  position: absolute;

  left: 14px;
  right: 14px;
  bottom: 3px;

  height: 2px;

  background: #00a9ac;

  border-radius: 2px;
}

/* =========================
   LOGIN BUTTON
========================= */

.navbar-login {
  color: #ffffff !important;

  background: #00a9ac !important;

  padding: 9px 18px !important;

  border-radius: 7px !important;

  font-weight: 600 !important;

  margin-left: 4px;

  transition:
    background 0.2s ease,
    transform 0.2s ease !important;
}

.navbar-login:hover {
  color: #ffffff !important;

  background: #008f92 !important;

  transform: translateY(-1px);
}

/* Remove active styling from Login */

.navbar-login.router-link-active {
  color: #ffffff !important;
  background: #00a9ac !important;
}

.navbar-login.router-link-active::after {
  display: none;
}

/* =========================
   TABLET
========================= */

@media (max-width: 700px) {
  .navbar {
    padding: 0 20px;
  }

  .navbar-links {
    gap: 3px;
  }

  .navbar-links a {
    font-size: 0.85rem;
    padding: 8px 9px;
  }

  .navbar-login {
    padding: 8px 13px !important;
  }
}

/* =========================
   MOBILE
========================= */

@media (max-width: 500px) {
  .navbar {
    height: 58px;

    padding: 0 12px;
  }

  .navbar-brand {
    font-size: 1.15rem;
  }

  .navbar-links {
    gap: 1px;
  }

  .navbar-links a {
    font-size: 0.72rem;

    padding: 7px 6px;
  }

  .navbar-links a.router-link-active::after {
    left: 6px;
    right: 6px;
  }

  .navbar-login {
    padding: 7px 9px !important;

    margin-left: 2px;
  }
}
</style>