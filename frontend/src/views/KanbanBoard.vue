<template>
  <div class="kanban-container">
    <header class="board-header" :style="{ borderBottomColor: board?.background_color }">
      <div class="header-left">
        <button @click="$router.push('/boards')" class="btn-back">← Retour</button>
        <h1>{{ board?.name || 'Chargement...' }}</h1>
        <span v-if="board?.is_public" class="badge-public">Public</span>
      </div>
      <button @click="showAddList = true" class="btn-primary">+ Ajouter une liste</button>
    </header>

    <div v-if="loading" class="loading">Chargement du tableau...</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <div v-else class="lists-container">
      <div
        v-for="list in lists"
        :key="list.id"
        class="kanban-list"
      >
        <div class="list-header">
          <h3>{{ list.name }}</h3>
          <span class="card-count">{{ getCardsForList(list.id).length }}</span>
        </div>

        <div
          :data-list-id="list.id"
          class="cards-container"
        >
          <div
            v-for="card in getCardsForList(list.id)"
            :key="card.id"
            :data-card-id="card.id"
            class="kanban-card"
            @click="openCard(card)"
          >
            <h4>{{ card.title }}</h4>
            <p v-if="card.description">{{ card.description }}</p>
            <div v-if="card.labels && card.labels.length > 0" class="card-labels">
              <span
                v-for="label in card.labels"
                :key="label.id"
                class="label-tag"
                :style="{ backgroundColor: label.color }"
              >
                {{ label.name }}
              </span>
            </div>
            <div v-if="card.due_date" class="card-due-date">
              📅 {{ formatDate(card.due_date) }}
            </div>
          </div>
        </div>

        <button @click="showAddCard(list.id)" class="btn-add-card">
          + Ajouter une carte
        </button>
      </div>

      <div v-if="lists.length === 0" class="empty-lists">
        <p>Aucune liste. Commencez par créer une liste !</p>
      </div>
    </div>

    <!-- Modal Ajouter Liste -->
    <div v-if="showAddList" class="modal-overlay" @click="showAddList = false">
      <div class="modal" @click.stop>
        <h2>Nouvelle Liste</h2>
        <form @submit.prevent="createList">
          <div class="form-group">
            <label>Nom de la liste *</label>
            <input
              v-model="newList.name"
              type="text"
              required
              placeholder="À faire, En cours, Terminé..."
              maxlength="100"
              autofocus
            />
          </div>
          <div class="modal-actions">
            <button type="button" @click="showAddList = false" class="btn-secondary">
              Annuler
            </button>
            <button type="submit" class="btn-primary" :disabled="!newList.name">
              Créer
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal Ajouter Carte -->
    <div v-if="showCardModal" class="modal-overlay" @click="showCardModal = false">
      <div class="modal" @click.stop>
        <h2>{{ editingCard ? 'Modifier la carte' : 'Nouvelle Carte' }}</h2>
        <form @submit.prevent="saveCard">
          <div class="form-group">
            <label>Titre *</label>
            <input
              v-model="cardForm.title"
              type="text"
              required
              placeholder="Titre de la carte"
              maxlength="200"
            />
          </div>

          <div class="form-group">
            <label>Description</label>
            <textarea
              v-model="cardForm.description"
              placeholder="Description détaillée..."
              rows="4"
            ></textarea>
          </div>

          <div class="form-group">
            <label>Date d'échéance</label>
            <input
              v-model="cardForm.due_date"
              type="datetime-local"
            />
          </div>

          <div class="modal-actions">
            <button
              v-if="editingCard"
              type="button"
              @click="deleteCard"
              class="btn-danger"
            >
              Supprimer
            </button>
            <button type="button" @click="closeCardModal" class="btn-secondary">
              Annuler
            </button>
            <button type="submit" class="btn-primary" :disabled="!cardForm.title">
              {{ editingCard ? 'Modifier' : 'Créer' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { getBoardById } from '../api/boards'
import { getAllLists, createList as createListAPI } from '../api/lists'
import { getListCards, createCard, updateCard, deleteCard as deleteCardAPI } from '../api/kanban-cards'
import Sortable from 'sortablejs'

export default {
  name: 'KanbanBoard',

  data() {
    return {
      board: null,
      lists: [],
      cards: [],
      loading: true,
      error: null,
      showAddList: false,
      showCardModal: false,
      editingCard: null,
      currentListId: null,
      newList: {
        name: '',
        position: 0
      },
      cardForm: {
        title: '',
        description: '',
        due_date: null,
        position: 0
      }
    }
  },

  async created() {
    await this.loadBoard()
  },

  mounted() {
    this.initDragAndDrop()
  },

  methods: {
    async loadBoard() {
      try {
        this.loading = true
        const boardId = this.$route.params.id

        this.board = await getBoardById(boardId)

        // Récupérer toutes les listes et filtrer par board_id
        const allLists = await getAllLists()
        this.lists = allLists.filter(list => list.board_id === boardId)

        // Charger les cartes pour chaque liste
        const cardsPromises = this.lists.map(list =>
          getListCards(list.id).then(cards => ({ listId: list.id, cards }))
        )

        const cardsResults = await Promise.all(cardsPromises)
        this.cards = cardsResults.flatMap(result => result.cards)

      } catch (err) {
        console.error('Error loading board:', err)
        this.error = 'Impossible de charger le tableau'

        if (err.response?.status === 401) {
          this.$router.push('/login')
        } else if (err.response?.status === 404) {
          this.error = 'Tableau non trouvé'
        }
      } finally {
        this.loading = false
      }
    },

    async createList() {
      try {
        const newList = await createListAPI({
          name: this.newList.name,
          position: this.lists.length,
          board_id: this.board.id
        })

        this.lists.push(newList)
        this.showAddList = false
        this.newList = { name: '', position: 0 }

        this.$nextTick(() => {
          this.initDragAndDrop()
        })
      } catch (err) {
        console.error('Error creating list:', err)
        alert('Erreur lors de la création de la liste')
      }
    },

    showAddCard(listId) {
      this.currentListId = listId
      this.editingCard = null
      this.cardForm = {
        title: '',
        description: '',
        due_date: null,
        position: this.getCardsForList(listId).length
      }
      this.showCardModal = true
    },

    openCard(card) {
      this.editingCard = card
      this.currentListId = card.list_id
      this.cardForm = {
        title: card.title,
        description: card.description || '',
        due_date: card.due_date ? new Date(card.due_date).toISOString().slice(0, 16) : null,
        position: card.position
      }
      this.showCardModal = true
    },

    async saveCard() {
      try {
        if (this.editingCard) {
          const updated = await updateCard(this.editingCard.id, this.cardForm)
          const index = this.cards.findIndex(c => c.id === this.editingCard.id)
          if (index !== -1) {
            this.cards.splice(index, 1, updated)
          }
        } else {
          const newCard = await createCard(this.currentListId, {
            ...this.cardForm,
            list_id: this.currentListId
          })
          this.cards.push(newCard)
        }

        this.closeCardModal()
      } catch (err) {
        console.error('Error saving card:', err)
        alert('Erreur lors de la sauvegarde de la carte')
      }
    },

    async deleteCard() {
      if (!confirm('Supprimer cette carte ?')) return

      try {
        await deleteCardAPI(this.editingCard.id)
        this.cards = this.cards.filter(c => c.id !== this.editingCard.id)
        this.closeCardModal()
      } catch (err) {
        console.error('Error deleting card:', err)
        alert('Erreur lors de la suppression de la carte')
      }
    },

    closeCardModal() {
      this.showCardModal = false
      this.editingCard = null
      this.currentListId = null
    },

    getCardsForList(listId) {
      return this.cards
        .filter(card => card.list_id === listId)
        .sort((a, b) => a.position - b.position)
    },

    initDragAndDrop() {
      this.$nextTick(() => {
        const containers = document.querySelectorAll('.cards-container')

        containers.forEach(container => {
          new Sortable(container, {
            group: 'cards',
            animation: 150,
            ghostClass: 'sortable-ghost',
            dragClass: 'sortable-drag',
            onEnd: this.handleCardDrop
          })
        })
      })
    },

    async handleCardDrop(evt) {
      const cardId = parseInt(evt.item.dataset.cardId)
      const newListId = parseInt(evt.to.dataset.listId)
      const newPosition = evt.newIndex

      const card = this.cards.find(c => c.id === cardId)
      if (!card) return

      try {
        card.list_id = newListId
        card.position = newPosition

        await updateCard(cardId, {
          list_id: newListId,
          position: newPosition
        })
      } catch (err) {
        console.error('Error moving card:', err)
        await this.loadBoard()
      }
    },

    formatDate(dateString) {
      const date = new Date(dateString)
      return date.toLocaleDateString('fr-FR', {
        day: 'numeric',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
  }
}
</script>

<style scoped>
.kanban-container {
  min-height: 100vh;
  background: #f5f6f8;
  display: flex;
  flex-direction: column;
}

.board-header {
  background: white;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 3px solid #3498db;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.btn-back {
  background: #ecf0f1;
  border: none;
  padding: 8px 15px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1em;
  transition: background 0.2s;
}

.btn-back:hover {
  background: #d5dbdb;
}

.board-header h1 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.8em;
}

.badge-public {
  padding: 4px 12px;
  background: #d4edda;
  color: #155724;
  border-radius: 12px;
  font-size: 0.85em;
  font-weight: 600;
}

.lists-container {
  display: flex;
  gap: 20px;
  padding: 20px;
  overflow-x: auto;
  flex: 1;
}

.kanban-list {
  background: #ebecf0;
  border-radius: 8px;
  padding: 10px;
  min-width: 300px;
  max-width: 300px;
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 120px);
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  margin-bottom: 10px;
}

.list-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.1em;
}

.card-count {
  background: #95a5a6;
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.85em;
  font-weight: 600;
}

.cards-container {
  flex: 1;
  overflow-y: auto;
  min-height: 50px;
  padding: 5px;
}

.kanban-card {
  background: white;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.kanban-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.15);
}

.kanban-card h4 {
  margin: 0 0 8px 0;
  color: #2c3e50;
  font-size: 1em;
}

.kanban-card p {
  margin: 0 0 8px 0;
  color: #7f8c8d;
  font-size: 0.9em;
  line-height: 1.4;
  max-height: 60px;
  overflow: hidden;
}

.card-labels {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}

.label-tag {
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 0.75em;
  color: white;
  font-weight: 600;
}

.card-due-date {
  font-size: 0.85em;
  color: #e74c3c;
  font-weight: 500;
}

.btn-add-card {
  background: transparent;
  border: none;
  color: #5e6c84;
  padding: 10px;
  text-align: left;
  cursor: pointer;
  border-radius: 6px;
  transition: background 0.2s;
  font-size: 0.95em;
}

.btn-add-card:hover {
  background: #d5dbe0;
}

.sortable-ghost {
  opacity: 0.4;
  background: #c8ebfb;
}

.sortable-drag {
  opacity: 0.9;
}

.empty-lists {
  text-align: center;
  padding: 60px 20px;
  color: #95a5a6;
  width: 100%;
}

.loading, .error {
  text-align: center;
  padding: 60px 20px;
  font-size: 1.2em;
}

.error {
  color: #e74c3c;
}

/* Modal styles */
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

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  font-size: 1em;
  font-family: inherit;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #3498db;
}

.modal-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 25px;
}

.btn-primary, .btn-secondary, .btn-danger {
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

.btn-danger {
  background: #e74c3c;
  color: white;
  margin-right: auto;
}

.btn-danger:hover {
  background: #c0392b;
}
</style>
