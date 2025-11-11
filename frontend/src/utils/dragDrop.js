// frontend/src/utils/dragDrop.js
// Utilitaires pour la gestion du glisser-déposer avec SortableJS

import Sortable from 'sortablejs';

// Clés par défaut pour le localStorage
const DEFAULT_STORAGE_KEY = 'sortable-order';
const DEFAULT_GROUP_NAME = 'shared';

/**
 * Configuration par défaut pour les instances Sortable
 */
const DEFAULT_CONFIG = {
  animation: 150,
  ghostClass: 'sortable-ghost',
  chosenClass: 'sortable-chosen',
  dragClass: 'sortable-drag',
  handle: null,
  filter: '.no-drag',
  preventOnFilter: true,
  dragoverBubble: true,
  dataIdAttr: 'data-id',
};

/**
 * Crée une instance Sortable avec configuration par défaut
 * @param {string|HTMLElement} element - Sélecteur ou élément DOM
 * @param {Object} options - Options supplémentaires pour SortableJS
 * @returns {Sortable} Instance Sortable créée
 */
export function createSortableInstance(element, options = {}) {
  const el = typeof element === 'string' ? document.querySelector(element) : element;
  
  if (!el) {
    throw new Error(`Élément non trouvé : ${element}`);
  }

  const config = {
    ...DEFAULT_CONFIG,
    ...options,
    onStart: (evt) => handleDragStart(evt, options.onStart),
    onEnd: (evt) => handleDragEnd(evt, options.onEnd),
    onUpdate: (evt) => handleUpdate(evt, options.onUpdate),
  };

  return new Sortable(el, config);
}

/**
 * Gestionnaire pour l'événement drag start
 * @param {SortableEvent} evt - Événement Sortable
 * @param {Function} customCallback - Callback utilisateur optionnel
 */
function handleDragStart(evt, customCallback) {
  evt.item.classList.add('dragging');
  document.body.style.cursor = 'grabbing';
  
  // Dispatch un événement custom
  evt.item.dispatchEvent(new CustomEvent('sortable:start', { 
    detail: { evt },
    bubbles: true 
  }));

  if (customCallback) customCallback(evt);
}

/**
 * Gestionnaire pour l'événement drag end
 * @param {SortableEvent} evt - Événement Sortable
 * @param {Function} customCallback - Callback utilisateur optionnel
 */
function handleDragEnd(evt, customCallback) {
  evt.item.classList.remove('dragging');
  document.body.style.cursor = '';
  
  // Dispatch un événement custom
  evt.item.dispatchEvent(new CustomEvent('sortable:end', { 
    detail: { evt },
    bubbles: true 
  }));

  if (customCallback) customCallback(evt);
}

/**
 * Gestionnaire pour l'événement update (ordre modifié)
 * @param {SortableEvent} evt - Événement Sortable
 * @param {Function} customCallback - Callback utilisateur optionnel
 */
async function handleUpdate(evt, customCallback) {
  const container = evt.to;
  const item = evt.item;
  
  // Dispatch un événement custom
  container.dispatchEvent(new CustomEvent('sortable:update', { 
    detail: { evt, item },
    bubbles: true 
  }));

  // Sauvegarde automatique si une clé de stockage est fournie
  const sortable = evt.target.sortable || evt.to.sortable;
  if (sortable && sortable.options.storageKey) {
    saveOrder(container, sortable.options.storageKey);
  }

  if (customCallback) customCallback(evt);
}

/**
 * Sauvegarde l'ordre des éléments dans localStorage
 * @param {HTMLElement} container - Conteneur Sortable
 * @param {string} storageKey - Clé de stockage
 * @param {string} attribute - Attribut pour identifier les éléments (data-id par défaut)
 */
export function saveOrder(container, storageKey = DEFAULT_STORAGE_KEY, attribute = 'data-id') {
  try {
    const order = Array.from(container.children)
      .map(child => child.getAttribute(attribute))
      .filter(id => id !== null);
    
    localStorage.setItem(storageKey, JSON.stringify(order));
    
    // Dispatch un événement de confirmation
    container.dispatchEvent(new CustomEvent('sortable:saved', { 
      detail: { order, storageKey },
      bubbles: true 
    }));
  } catch (error) {
    console.error('Erreur lors de la sauvegarde de l\'ordre:', error);
  }
}

/**
 * Charge et restaure l'ordre des éléments depuis localStorage
 * @param {HTMLElement} container - Conteneur Sortable
 * @param {string} storageKey - Clé de stockage
 * @param {string} attribute - Attribut pour identifier les éléments
 */
export function loadOrder(container, storageKey = DEFAULT_STORAGE_KEY, attribute = 'data-id') {
  try {
    const savedOrder = localStorage.getItem(storageKey);
    if (!savedOrder) return false;

    const order = JSON.parse(savedOrder);
    const children = Array.from(container.children);
    
    // Crée une map des éléments par leur ID
    const elementMap = new Map();
    children.forEach(child => {
      const id = child.getAttribute(attribute);
      if (id) elementMap.set(id, child);
    });

    // Réorganise les éléments selon l'ordre sauvegardé
    order.forEach(id => {
      const element = elementMap.get(id);
      if (element) {
        container.appendChild(element);
        elementMap.delete(id);
      }
    });

    // Ajoute les éléments restants (nouveaux éléments non dans le storage)
    elementMap.forEach(element => container.appendChild(element));

    // Dispatch un événement de confirmation
    container.dispatchEvent(new CustomEvent('sortable:loaded', { 
      detail: { order },
      bubbles: true 
    }));

    return true;
  } catch (error) {
    console.error('Erreur lors du chargement de l\'ordre:', error);
    return false;
  }
}

/**
 * Récupère l'ordre actuel des éléments
 * @param {HTMLElement} container - Conteneur Sortable
 * @param {string} attribute - Attribut pour identifier les éléments
 * @returns {Array<string>} Tableau des IDs dans l'ordre actuel
 */
export function getOrder(container, attribute = 'data-id') {
  return Array.from(container.children)
    .map(child => child.getAttribute(attribute))
    .filter(id => id !== null);
}

/**
 * Réinitialise l'ordre des éléments à l'état initial
 * @param {HTMLElement} container - Conteneur Sortable
 * @param {string} storageKey - Clé de stockage à supprimer
 */
export function resetOrder(container, storageKey = DEFAULT_STORAGE_KEY) {
  try {
    localStorage.removeItem(storageKey);
    
    // Dispatch un événement de confirmation
    container.dispatchEvent(new CustomEvent('sortable:reset', { 
      bubbles: true 
    }));
    
    return true;
  } catch (error) {
    console.error('Erreur lors de la réinitialisation:', error);
    return false;
  }
}

/**
 * Détruit proprement une instance Sortable
 * @param {Sortable} sortableInstance - Instance à détruire
 */
export function destroySortable(sortableInstance) {
  if (sortableInstance && typeof sortableInstance.destroy === 'function') {
    sortableInstance.destroy();
  }
}

/**
 * Crée un groupe de partage entre plusieurs listes
 * @param {Array<string|HTMLElement>} containers - Tableau de sélecteurs ou éléments
 * @param {string} groupName - Nom du groupe
 * @param {Object} options - Options supplémentaires
 * @returns {Array<Sortable>} Tableau des instances créées
 */
export function createSharedGroup(containers, groupName = DEFAULT_GROUP_NAME, options = {}) {
  return containers.map(container => {
    return createSortableInstance(container, {
      ...options,
      group: {
        name: groupName,
        pull: true,
        put: true,
        ...options.group,
      },
    });
  });
}

/**
 * Vérifie si un glisser-déposer est autorisé entre deux conteneurs
 * @param {HTMLElement} from - Conteneur source
 * @param {HTMLElement} to - Conteneur cible
 * @param {string} groupName - Nom du groupe attendu
 * @returns {boolean}
 */
export function isDragAllowed(from, to, groupName) {
  const fromSortable = from.sortable;
  const toSortable = to.sortable;
  
  if (!fromSortable || !toSortable) return false;
  
  const fromGroup = fromSortable.options.group;
  const toGroup = toSortable.options.group;
  
  if (typeof fromGroup === 'string' && typeof toGroup === 'string') {
    return fromGroup === toGroup && fromGroup === groupName;
  }
  
  if (typeof fromGroup === 'object' && typeof toGroup === 'object') {
    return fromGroup.name === toGroup.name && fromGroup.name === groupName;
  }
  
  return false;
}

// Export des constantes pour utilisation externe
export { DEFAULT_STORAGE_KEY, DEFAULT_GROUP_NAME };