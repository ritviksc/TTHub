<script setup>
import AuditLog from '@/components/audit/AuditLog.vue'
import { auth } from '@/stores/auth.js'
</script>

<template><AuditLog back-route="bm-administration" :branch-id="auth.user?.branch?.id" :branch-name="auth.user?.branch?.name ?? 'Your branch'" /></template>
