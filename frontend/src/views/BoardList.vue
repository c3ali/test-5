<template>
  <div class="board-list-container">
    <header class="header">
      <h1>Mes Tableaux Kanban</h1>
      <button @click="showCreateModal = true" class="btn-primary">
        + Nouveau Tableau
      </button>
    </header>

    <div v-if="loading" class="loading">
      Chargement...
    </div>

    <div v-else-if="error" class="error">
      {{ error }}
    </div>

    <div v-else class="boards-grid">
      <div
        v-for="board in boards"
        :key="board.id"
        class="board-card"
        :style="{ borderTopColor: board.background_color }"
        @click="openBoard(board.id)"
      >
        <h3>{{ board.name }}</h3>
        <p v-if="board.description">{{ board.description }}</p>
        <div class="board-footer">
          <span class="badge" :class="{ 'badge-public': board.is_public }">
            {{ board.is_public ? 'Public' : 'Privé' }}
          </span>
          <span class="created-date">
            {{ formatDate(board.created_at) }}
          </span>
        </div>
      </div>

      <div v-if="boards.length === 0" class="empty-state">
        <p>Aucun tableau pour le moment</p>
        <button @click="showCreateModal = true" class="btn-secondary">
          Créer votre premier tableau
        </button>
      </div>
    </div>

    <!-- Modal création tableau -->
    <div v-if="showCreateModal" class="modal-overlay" @click="showCreateModal = false">
      <div class="modal" @click.stop>
        <h2>Nouveau Tableau</h2>
        <form @submit.prevent="createNewBoard">
          <div class="form-group">
            <label>Nom du tableau *</label>
            <input
              v-model="newBoard.name"
              type="text"
              required
              placeholder="Mon projet"
              maxlength="100"
            />
          </div>

          <div class="form-group">
            <label>Description</label>
            <textarea
              v-model="newBoard.description"
              placeholder="Description du tableau..."
              rows="3"
            ></textarea>
          </div>

          <div class="form-group">
            <label>Couleur</label>
            <div class="color-picker">
              <div
                v-for="color in colors"
                :key="color"
                class="color-option"
                :class="{ active: newBoard.background_color === color }"
                :style="{ backgroundColor: color }"
                @click="newBoard.background_color = color"
              ></div>
            </div>
          </div>

          <div class="form-group">
            <label>
              <input type="checkbox" v-model="newBoard.is_public" />
              Rendre ce tableau public
            </label>
          </div>

          <div class="modal-actions">
            <button type="button" @click="showCreateModal = false" class="btn-secondary">
              Annuler
            </button>
            <button type="submit" class="btn-primary" :disabled="!newBoard.name">
              Créer
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { getAllBoards, createBoard } from '../api/boards'

export default {
  name: 'BoardList',

  data() {
    return {
      boards: [],
      loading: true,
      error: null,
      showCreateModal: false,
      newBoard: {
        name: '',
        description: '',
        background_color: '#3498db',
        is_public: false
      },
      colors: [
        '#3498db', '#e74c3c', '#2ecc71', '#f39c12',
        '#9b59b6', '#1abc9c', '#34495e', '#e67e22'
      ]
    }
  },

  async created() {
    await this.loadBoards()
  },

  methods: {
    async loadBoards() {
      try {
        this.loading = true
        this.error = null
        this.boards = await getAllBoards()
      } catch (err) {
        console.error('Error loading boards:', err)
        this.error = 'Impossible de charger les tableaux'

        if (err.response?.status === 401) {
          this.$router.push('/login')
        }
      } finally {
        this.loading = false
      }
    },

    async createNewBoard() {
      try {
        const board = await createBoard(this.newBoard)
        this.boards.push(board)
        this.showCreateModal = false
        this.newBoard = {
          name: '',
          description: '',
          background_color: '#3498db',
          is_public: false
        }
        // Ouvrir le nouveau tableau
        this.$router.push(`/board/${board.id}`)
      } catch (err) {
        console.error('Error creating board:', err)
        alert('Erreur lors de la création du tableau')
      }
    },

    openBoard(boardId) {
      this.$router.push(`/board/${boardId}`)
    },

    formatDate(dateString) {
      const date = new Date(dateString)
      return date.toLocaleDateString('fr-FR', {
        day: 'numeric',
        month: 'short',
        year: 'numeric'
      })
    }
  }
}
</script>

<style scoped>
.board-list-container {
  min-height: 100vh;
  background: #f5f6f8;
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 0 10px;
}

.header h1 {
  color: #2c3e50;
  margin: 0;
}

.boards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  padding: 10px;
}

.board-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  border-top: 4px solid #3498db;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.board-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.board-card h3 {
  margin: 0 0 10px 0;
  color: #2c3e50;
  font-size: 1.3em;
}

.board-card p {
  color: #7f8c8d;
  margin: 0 0 15px 0;
  font-size: 0.95em;
  line-height: 1.5;
}

.board-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85em;
  color: #95a5a6;
}

.badge {
  padding: 4px 10px;
  border-radius: 12px;
  background: #ecf0f1;
  color: #7f8c8d;
  font-size: 0.9em;
}

.badge-public {
  background: #d4edda;
  color: #155724;
}

.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 60px 20px;
  color: #95a5a6;
}

.loading, .error {
  text-align: center;
  padding: 60px 20px;
  font-size: 1.2em;
}

.error {
  color: #e74c3c;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  padding: 30px;
  border-radius: 10px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal h2 {
  margin: 0 0 20px 0;
  color: #2c3e50;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #555;
  font-weight: 500;
}

.form-group input[type="text"],
.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  font-size: 1em;
  font-family: inherit;
}

.form-group input[type="text"]:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #3498db;
}

.color-picker {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.color-option {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  cursor: pointer;
  transition: transform 0.2s;
  border: 3px solid transparent;
}

.color-option:hover {
  transform: scale(1.1);
}

.color-option.active {
  border-color: #2c3e50;
  transform: scale(1.15);
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 25px;
}

.btn-primary, .btn-secondary {
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 1em;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.btn-primary {
  background: #3498db;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2980b9;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #ecf0f1;
  color: #2c3e50;
}

.btn-secondary:hover {
  background: #d5dbdb;
}
</style>
