<template>
  <v-container fluid>
    <v-card>
      <v-card-title class="text-h6">Referential Data</v-card-title>
      <v-tabs v-model="tab" bg-color="primary" dark>
        <v-tab v-for="t in tabs" :key="t.key">{{ t.label }}</v-tab>
      </v-tabs>

      <v-card-text>
        <v-window v-model="tab">
          <v-window-item v-for="(t, i) in tabs" :key="t.key" :value="i">
            <generic-ref-tab
              :title="t.label"
              :resource="t.resource"
              :columns="t.columns"
              :fields="t.fields"
              :default-sort="t.defaultSort || 'id:asc'"
            />
          </v-window-item>
        </v-window>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import GenericRefTab from '@/components/GenericRefTab.vue'

const tab = ref(0)

// columns = table display; fields = form fields
const tabs = [
  {
    key: 'currency',
    label: 'Currency',
    resource: 'currencies',
    defaultSort: 'code:asc',
    columns: [
      { key: 'code', title: 'Code' },
      { key: 'name', title: 'Name' },
    ],
    fields: [
      { key: 'code', label: 'Code', required: true, maxlength: 3 },
      { key: 'name', label: 'Name' },
    ],
  },
  {
    key: 'country',
    label: 'Country',
    resource: 'countries',
    defaultSort: 'name:asc',
    columns: [
      { key: 'iso2', title: 'ISO2' },
      { key: 'iso3', title: 'ISO3' },
      { key: 'name', title: 'Name' },
    ],
    fields: [
      { key: 'iso2', label: 'ISO2', required: true, maxlength: 2 },
      { key: 'iso3', label: 'ISO3', maxlength: 3 },
      { key: 'name', label: 'Name' },
    ],
  },
  {
    key: 'sector',
    label: 'Sector',
    resource: 'sectors',
    defaultSort: 'code:asc',
    columns: [
      { key: 'code', title: 'Code' },
      { key: 'label', title: 'Label' },
      { key: 'description', title: 'Description' },
    ],
    fields: [
      { key: 'code', label: 'Code', required: true },
      { key: 'label', label: 'Label', required: true },
      { key: 'description', label: 'Description', type: 'textarea' },
    ],
  },
  {
    key: 'pra',
    label: 'PRA Activity',
    resource: 'pra-activities',
    defaultSort: 'code:asc',
    columns: [
      { key: 'code', title: 'Code' },
      { key: 'label', title: 'Label' },
      { key: 'description', title: 'Description' },
    ],
    fields: [
      { key: 'code', label: 'Code', required: true },
      { key: 'label', label: 'Label', required: true },
      { key: 'description', label: 'Description', type: 'textarea' },
    ],
  },
  {
    key: 'cptytype',
    label: 'Counterparty Type',
    resource: 'counterparty-types',
    defaultSort: 'code:asc',
    columns: [
      { key: 'code', title: 'Code' },
      { key: 'label', title: 'Label' },
      { key: 'description', title: 'Description' },
    ],
    fields: [
      { key: 'code', label: 'Code', required: true },
      { key: 'label', label: 'Label', required: true },
      { key: 'description', label: 'Description', type: 'textarea' },
    ],
  },
  {
    key: 'insttype',
    label: 'Instrument Type',
    resource: 'instrument-types',
    defaultSort: 'code:asc',
    columns: [
      { key: 'code', title: 'Code' },
      { key: 'label', title: 'Label' },
      { key: 'description', title: 'Description' },
    ],
    fields: [
      { key: 'code', label: 'Code', required: true },
      { key: 'label', label: 'Label', required: true },
      { key: 'description', label: 'Description', type: 'textarea' },
    ],
  },
  {
    key: 'facType',
    label: 'Facility Type',
    resource: 'facility-types',
    defaultSort: 'code:asc',
    columns: [
      { key: 'code', title: 'Code' },
      { key: 'label', title: 'Label' },
      { key: 'description', title: 'Description' },
    ],
    fields: [
      { key: 'code', label: 'Code', required: true },
      { key: 'label', label: 'Label', required: true },
      { key: 'description', label: 'Description', type: 'textarea' },
    ],
  },
]
</script>
