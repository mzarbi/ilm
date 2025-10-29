import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import { aliases, mdi } from 'vuetify/iconsets/mdi'

// Import the actual CSS for Material Design Icons
import '@mdi/font/css/materialdesignicons.css'

export default createVuetify({
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: { mdi },
  },
  theme: {
    defaultTheme: 'light',
    themes: {
      light: {
        colors: {
          primary: '#1e88e5',
          secondary: '#26a69a',
          error: '#e53935',
          success: '#43a047',
          warning: '#fdd835',
        },
      },
    },
  },
})
