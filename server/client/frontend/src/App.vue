<template>
  <v-app>
    <v-layout>
      <v-app-bar color="primary" prominent>
        <v-app-bar-title>DH Interlinkages</v-app-bar-title>
        <v-spacer />
        <v-btn variant="text" @click="$router.push({ name: 'interlinkages' })" prepend-icon="mdi-domain">Interlinkages</v-btn>
        <v-btn variant="text" prepend-icon="mdi-clipboard-text" @click="$router.push({ name: 'fi' })">
          Facilities & Instruments
        </v-btn>
        <v-btn variant="text" prepend-icon="mdi-briefcase" @click="$router.push({ name: 'projects' })">
          Projects
        </v-btn>

        <v-btn variant="text" @click="$router.push({ name: 'entities' })" prepend-icon="mdi-domain">Entities</v-btn>

        <v-btn
          variant="elevated"
          color="white"
          prepend-icon="mdi-database-cog"
          @click="$router.push({ name: 'refs' })"
          style="    margin-right: 1rem;"
        >
          Referentials
        </v-btn>
      </v-app-bar>

      <v-main class="pa-6 pt-16">
        <router-view />
      </v-main>
    </v-layout>
  </v-app>
</template>

<script setup>
// nothing special here — router is automatically injected
</script>
