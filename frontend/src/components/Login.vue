<template>
  <div class="login-container">
    <div class="login-card">
      <h1>Kanban Board</h1>
      <h2>{{ isRegister ? 'Créer un compte' : 'Connexion' }}</h2>

      <form @submit.prevent="handleSubmit" class="login-form">
        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <div class="form-group">
          <label for="email">Email</label>
          <input
            id="email"
            v-model="form.email"
            type="email"
            required
            placeholder="votre@email.com"
            autocomplete="email"
          />
        </div>

        <div class="form-group">
          <label for="password">Mot de passe</label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            required
            :placeholder="isRegister ? 'Min. 8 caractères, 1 majuscule, 1 chiffre' : 'Votre mot de passe'"
            autocomplete="current-password"
          />
        </div>

        <div v-if="isRegister" class="form-group">
          <label for="first_name">Prénom (optionnel)</label>
          <input
            id="first_name"
            v-model="form.first_name"
            type="text"
            placeholder="Votre prénom"
          />
        </div>

        <div v-if="isRegister" class="form-group">
          <label for="last_name">Nom (optionnel)</label>
          <input
            id="last_name"
            v-model="form.last_name"
            type="text"
            placeholder="Votre nom"
          />
        </div>

        <button type="submit" class="btn-primary" :disabled="loading">
          {{ loading ? 'Chargement...' : (isRegister ? 'Créer un compte' : 'Se connecter') }}
        </button>
      </form>

      <p class="toggle-mode">
        {{ isRegister ? 'Vous avez déjà un compte ?' : 'Pas encore de compte ?' }}
        <a href="#" @click.prevent="toggleMode">
          {{ isRegister ? 'Se connecter' : 'Créer un compte' }}
        </a>
      </p>
    </div>
  </div>
</template>

<script>
import UsersService from '../api/users'

export default {
  name: 'Login',

  data() {
    return {
      isRegister: false,
      loading: false,
      error: null,
      form: {
        email: '',
        password: '',
        first_name: '',
        last_name: ''
      }
    }
  },

  methods: {
    toggleMode() {
      this.isRegister = !this.isRegister
      this.error = null
    },

    async handleSubmit() {
      this.error = null
      this.loading = true

      try {
        if (this.isRegister) {
          await UsersService.register(this.form)
        } else {
          await UsersService.login({
            email: this.form.email,
            password: this.form.password
          })
        }

        // Rediriger vers le dashboard (le token est déjà stocké par UsersService)
        this.$router.push('/boards')
      } catch (err) {
        console.error('Auth error:', err)
        this.error = err.message || 'Une erreur est survenue. Veuillez réessayer.'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-card {
  background: white;
  padding: 40px;
  border-radius: 10px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  width: 100%;
  max-width: 400px;
}

.login-card h1 {
  color: #667eea;
  margin: 0 0 10px 0;
  font-size: 2em;
  text-align: center;
}

.login-card h2 {
  margin: 0 0 30px 0;
  color: #333;
  font-size: 1.5em;
  text-align: center;
  font-weight: normal;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  color: #555;
  font-weight: 500;
  font-size: 0.9em;
}

.form-group input {
  padding: 12px;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  font-size: 1em;
  transition: border-color 0.3s;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 14px;
  border: none;
  border-radius: 6px;
  font-size: 1.1em;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-message {
  background: #fee;
  color: #c33;
  padding: 12px;
  border-radius: 6px;
  border-left: 4px solid #c33;
  font-size: 0.9em;
}

.toggle-mode {
  text-align: center;
  margin-top: 20px;
  color: #666;
}

.toggle-mode a {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
}

.toggle-mode a:hover {
  text-decoration: underline;
}
</style>
