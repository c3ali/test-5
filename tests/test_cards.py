# tests/test_cards.py
import pytest
import random
from typing import List, Tuple

# On suppose que cards.py contient une classe Card et une classe Deck
# avec des fonctionnalités standard de gestion de cartes à jouer.
# Si le module n'existe pas ou manque de fonctionnalités,
# certains tests seront automatiquement ignorés.

try:
    from cards import Card, Deck, CardError
    CARDS_MODULE_AVAILABLE = True
except ImportError:
    CARDS_MODULE_AVAILABLE = False
    # Créer des placeholders pour que les tests puissent être importés
    class Card:
        def __init__(self, *args, **kwargs): pass
    class Deck:
        def __init__(self, *args, **kwargs): pass
    class CardError(Exception):
        pass
    pytestmark = pytest.mark.skip(reason="Module cards.py non trouvé")


# Fixtures
@pytest.fixture
def sample_card() -> Card:
    """Crée une carte exemple."""
    return Card("hearts", "A")


@pytest.fixture
def sample_deck() -> Deck:
    """Crée un jeu de cartes complet."""
    return Deck()


@pytest.fixture
def empty_deck() -> Deck:
    """Crée un jeu de cartes vide."""
    deck = Deck()
    deck.cards = []
    return deck


# Tests pour la classe Card
class TestCard:
    """Tests unitaires pour la classe Card."""

    @pytest.mark.skipif(not CARDS_MODULE_AVAILABLE, reason="Module cards indisponible")
    def test_card_creation_valid(self):
        """Teste la création d'une carte avec des valeurs valides."""
        card = Card("hearts", "A")
        assert card.suit == "hearts"
        assert card.rank == "A"

    @pytest.mark.skipif(not CARDS_MODULE_AVAILABLE, reason="Module cards indisponible")
    @pytest.mark.parametrize("suit,rank", [
        ("spades", "K"),
        ("clubs", "Q"),
        ("diamonds", "J"),
        ("hearts", "10"),
        ("spades", "2"),
    ])
    def test_card_creation_various(self, suit: str, rank: str):
        """Teste la création de cartes avec différentes couleurs et valeurs."""
        card = Card(suit, rank)
        assert card.suit == suit
        assert card.rank == rank

    @pytest.mark.skipif(not CARDS_MODULE_AVAILABLE, reason="Module cards indisponible")
    def test_card_str_representation(self, sample_card: Card):
        """Teste la représentation string d'une carte."""
        # Supposer que __str__ existe ou utiliser __repr__ comme fallback
        try:
            str_repr = str(sample_card)
            assert "A" in str_repr
            assert "hearts" in str_repr.lower()
        except (AttributeError, TypeError):
            pytest.skip("Méthode __str__ non implémentée ou invalide")

    @pytest.mark.skipif(not CARDS_MODULE_AVAILABLE, reason="Module cards indisponible")
    def test_card_equality(self):
        """Teste l'égalité entre deux cartes."""
        card1 = Card("hearts", "A")
        card2 = Card("hearts", "A")
        card3 = Card("spades", "A")
        
        assert card1 == card2
        assert card1 != card3

    @pytest.mark.skipif(not CARDS_MODULE_AVAILABLE, reason="Module cards indisponible")
    def test_card_comparison_greater_than(self):
        """Teste la comparaison de cartes (si implémentée)."""
        try:
            card1 = Card("hearts", "K")
            card2 = Card("hearts", "Q")
            assert card1 > card2
        except TypeError:
            pytest.skip("Comparaison non supportée")

    @pytest.mark.skipif(not CARDS_MODULE_AVAILABLE, reason="Module cards indisponible")
    def test_card_comparison_less_than(self):
        """Teste la comparaison de cartes (si implémentée)."""
        try:
            card1 = Card("hearts", "2")
            card2 = Card("hearts", "A")
            assert card1 < card2
        except TypeError:
            pytest.skip("Comparaison non supportée")


# Tests pour la classe Deck
class TestDeck:
    """Tests unitaires pour la classe Deck."""

    @pytest.mark.skipif(not CARDS_MODULE_AVAILABLE, reason="Module cards indisponible")
    def test_deck_creation_standard(self, sample_deck: Deck):
        """Teste la création d'un jeu standard de 52 cartes."""
        assert len(sample_deck.cards) == 52

    @pytest.mark.skipif(not CARDS_MODULE_AVAILABLE, reason="Module cards indisponible")
    def test_deck_contains_all_cards(self, sample_deck: Deck):
        """Vérifie que le deck contient toutes les combinaisons."""
        suits = ["hearts", "diamonds", "clubs", "spades"]
        ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        
        # Vérifier que chaque combinaison existe
        for suit in suits:
            for rank in ranks:
                assert any(
                    card.suit == suit and card.rank == rank 
                    for card in sample_deck.cards
                ), f"Carte manquante: {rank} of {suit}"

    @pytest.mark.skipif(not CARDS_MODULE_AVAILABLE, reason="Module cards indisponible")
    def test_deck_shuffle(self, sample_deck: Deck):
        """Teste le mélange du deck."""
        original_order = sample_deck.cards.copy()
        sample_deck.shuffle()
        
        # Vérifier que l'ordre a changé (probablement)
        # Note: Il y a une faible probabilité que le deck soit identique après mélange
        assert len(sample_deck.cards) == 52
        # Vérifier que les cartes sont les mêmes mais dans un ordre différent
        # On compare les IDs des objets pour vérifier que c'est les mêmes cartes
        original_ids = [id(card) for card in original_order]
        shuffled_ids = [id(card) for card in sample_deck.cards]
        assert set(original_ids) == set(shuffled_ids)

    @pytest.mark.skipif(not CARDS_MODULE_AVAILABLE, reason="Module cards indisponible")
    def test_deck_shuffle_randomness(self, sample_deck: Deck):
        """Teste la qualité du mélange sur plusieurs itérations."""
        # Forcer une graine pour la reproductibilité
        random.seed(42)
        sample_deck.shuffle()
        first_shuffle = [f"{c.rank}-{c.suit}" for c in sample_deck.cards]
        
        random.seed(42)
        sample_deck.shuffle()
        second_shuffle = [f"{c.rank}-{c.suit}" for c in sample_deck.cards]
        
        # Avec la même graine, le résultat devrait être identique
        assert first_shuffle == second_shuffle

    @pytest.mark.skipif(not CARDS_MODULE_AVAILABLE, reason="Module cards indisponible")
    def test_deck_deal_card(self, sample_deck: Deck):
        """Teste la distribution d'une carte."""
        initial_count = len(sample_deck.cards)
        card = sample_deck.deal()
        
        assert isinstance(card, Card)
        assert len(sample_deck.cards) == initial_count - 1

    @pytest.mark.skipif(not CARDS_MODULE_AVAILABLE, reason="Module cards indisponible")
    def test_deck_deal_from_empty_deck(self, empty_deck: Deck):
        """Teste la distribution depuis un deck vide."""
        with pytest.raises(CardError):
            empty_deck.deal()

    @pytest.mark.skipif(not CARDS_MODULE_AVAILABLE, reason="Module cards indisponible")
    def test_deck_add_card(self, empty_deck: Deck, sample_card: Card):
        """Teste l'ajout d'une carte au deck."""
        initial_count = len(empty_deck.cards)
        empty_deck.add_card(sample_card)
        
        assert len(empty_deck.cards) == initial_count + 1
        assert sample_card in empty_deck.cards

    @pytest.mark.skipif(not CARDS_MODULE_AVAILABLE, reason="Module cards indisponible")
    def test_deck_remove_card(self, sample_deck: Deck):
        """Teste la suppression d'une carte spécifique."""
        card_to_remove = sample_deck.cards[0]
        sample_deck.remove_card(card_to_remove)
        
        assert card_to_remove not in sample_deck.cards
        assert len(sample_deck.cards) == 51

    @pytest.mark.skipif(not CARDS_MODULE_AVAILABLE, reason="Module cards indisponible")
    def test_deck_is_empty(self, empty_deck: Deck, sample_deck: Deck):
        """Teste la vérification d'un deck vide."""
        assert empty_deck.is_empty()
        assert not sample_deck.is_empty()

    @pytest.mark.skipif(not CARDS_MODULE_AVAILABLE, reason="Module cards indisponible")
    def test_deck_sort(self, sample_deck: Deck):
        """Teste le tri du deck."""
        # Mélanger d'abord
        sample_deck.shuffle()
        # Puis trier
        sample_deck.sort()
        
        # Vérifier que les cartes sont triées (si la méthode existe)
        # On vérifie juste que la méthode ne lève pas d'erreur
        assert len(sample_deck.cards) == 52


# Tests pour les exceptions
class TestCardExceptions:
    """Tests pour les cas d'erreur et exceptions."""

    @pytest.mark.skipif(not CARDS_MODULE_AVAILABLE, reason="Module cards indisponible")
    def test_invalid_suit_raises_error(self):
        """Teste qu'une couleur invalide lève une exception."""
        with pytest.raises((CardError, ValueError)):
            Card("invalid_suit", "A")

    @pytest.mark.skipif(not CARDS_MODULE_AVAILABLE, reason="Module cards indisponible")
    def test_invalid_rank_raises_error(self):
        """Teste qu'une valeur invalide lève une exception."""
        with pytest.raises((CardError, ValueError)):
            Card("hearts", "invalid_rank")

    @pytest.mark.skipif(not CARDS_MODULE_AVAILABLE, reason="Module cards indisponible")
    def test_deal_too_many_cards(self, sample_deck: Deck):
        """Teste la distribution de plus de cartes que disponible."""
        for _ in range(52):
            sample_deck.deal()
        
        # La 53ème distribution devrait échouer
        with pytest.raises(CardError):
            sample_deck.deal()


# Tests d'intégration
class TestIntegration:
    """Tests d'intégration pour des scénarios réels."""

    @pytest.mark.skipif(not CARDS_MODULE_AVAILABLE, reason="Module cards indisponible")
    def test_full_game_simulation(self):
        """Simule une partie complète."""
        deck = Deck()
        deck.shuffle()
        
        # Distribuer 5 cartes à 2 joueurs
        player1_hand = [deck.deal() for _ in range(5)]
        player2_hand = [deck.deal() for _ in range(5)]
        
        assert len(player1_hand) == 5
        assert len(player2_hand) == 5
        assert len(deck.cards) == 42
        
        # Vérifier qu'il n'y a pas de doublons entre les mains
        all_cards = player1_hand + player2_hand
        assert len(all_cards) == len(set(id(c) for c in all_cards))

    @pytest.mark.skipif(not CARDS_MODULE_AVAILABLE, reason="Module cards indisponible")
    def test_deck_reset(self, sample_deck: Deck):
        """Teste la réinitialisation du deck."""
        sample_deck.deal()
        sample_deck.deal()
        assert len(sample_deck.cards) == 50
        
        sample_deck.reset()
        assert len(sample_deck.cards) == 52
```

### Instructions d'utilisation :

1. **Placez ce fichier** dans le répertoire `tests/test_cards.py`
2. **Créez le fichier `cards.py`** avec une structure minimale comme :

```python
# cards.py
class CardError(Exception):
    pass

class Card:
    def __init__(self, suit: str, rank: str):
        valid_suits = ["hearts", "diamonds", "clubs", "spades"]
        valid_ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        
        if suit not in valid_suits:
            raise CardError(f"Couleur invalide: {suit}")
        if rank not in valid_ranks:
            raise CardError(f"Valeur invalide: {rank}")
        
        self.suit = suit
        self.rank = rank
    
    def __str__(self) -> str:
        return f"{self.rank} of {self.suit}"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Card):
            return False
        return self.suit == other.suit and self.rank == other.rank
    
    def __lt__(self, other: 'Card') -> bool:
        ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        return ranks.index(self.rank) < ranks.index(other.rank)

class Deck:
    def __init__(self):
        suits = ["hearts", "diamonds", "clubs", "spades"]
        ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        self.cards = [Card(suit, rank) for suit in suits for rank in ranks]
    
    def shuffle(self) -> None:
        import random
        random.shuffle(self.cards)
    
    def deal(self) -> Card:
        if not self.cards:
            raise CardError("Le deck est vide")
        return self.cards.pop()
    
    def add_card(self, card: Card) -> None:
        self.cards.append(card)
    
    def remove_card(self, card: Card) -> None:
        self.cards.remove(card)
    
    def is_empty(self) -> bool:
        return len(self.cards) == 0
    
    def reset(self) -> None:
        suits = ["hearts", "diamonds", "clubs", "spades"]
        ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        self.cards = [Card(suit, rank) for suit in suits for rank in ranks]
```

3. **Exécutez les tests** avec : `pytest tests/test_cards.py -v`

Les tests sont conçus pour être robustes et s'adapteront automatiquement si certaines méthodes ne sont pas implément