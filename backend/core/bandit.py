"""
Multi-Armed Bandit para Aprendizaje por Refuerzo
Implementación de epsilon-greedy con Q-learning
"""

import numpy as np
import json
import random
import logging
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)


class MultiArmedBandit:
    """
    Multi-Armed Bandit con epsilon-greedy para aprendizaje por refuerzo

    Implementa:
    - Epsilon-greedy exploration/exploitation
    - Q-learning incremental
    - Persistencia de estado
    - Tracking de historial
    """

    def __init__(self, n_arms: int, epsilon: float = 0.2, learning_rate: float = None):
        """
        Inicializa el bandit

        Args:
            n_arms: Número de brazos (estrategias)
            epsilon: Probabilidad de exploración (0-1)
            learning_rate: Tasa de aprendizaje (None = promedio incremental)
        """
        self.n_arms = n_arms
        self.epsilon = epsilon
        self.learning_rate = learning_rate

        # Q-values y contadores
        self.q_values = np.zeros(n_arms)
        self.action_counts = np.zeros(n_arms)
        self.total_reward = 0

        # Historial
        self.history = []

        logger.info(f"Initialized Multi-Armed Bandit: arms={n_arms}, epsilon={epsilon}")

    def select_action(self, force_action: int = None) -> int:
        """
        Selecciona acción usando epsilon-greedy

        Args:
            force_action: Fuerza una acción específica (para testing)

        Returns:
            ID de la acción seleccionada
        """
        if force_action is not None:
            logger.debug(f"Forced action: {force_action}")
            return force_action

        # Epsilon-greedy
        if random.random() < self.epsilon:
            # Exploración: acción aleatoria
            action = random.randint(0, self.n_arms - 1)
            logger.debug(f"EXPLORATION: selected action {action}")
            return action
        else:
            # Explotación: mejor acción conocida
            action = int(np.argmax(self.q_values))
            logger.debug(f"EXPLOITATION: selected action {action} (Q={self.q_values[action]:.3f})")
            return action

    def update(self, action: int, reward: float):
        """
        Actualiza Q-values con nueva recompensa

        Args:
            action: Acción tomada
            reward: Recompensa recibida
        """
        self.action_counts[action] += 1
        self.total_reward += reward

        # Actualizar Q-value
        if self.learning_rate:
            # Q-learning con tasa de aprendizaje fija
            old_value = self.q_values[action]
            self.q_values[action] = old_value + self.learning_rate * (reward - old_value)
        else:
            # Promedio incremental (default)
            n = self.action_counts[action]
            old_value = self.q_values[action]
            self.q_values[action] = old_value + (reward - old_value) / n

        # Guardar en historial
        self.history.append({
            'action': int(action),
            'reward': float(reward),
            'q_value': float(self.q_values[action]),
            'count': int(self.action_counts[action]),
            'timestamp': datetime.now().isoformat()
        })

        logger.info(
            f"Updated action {action}: reward={reward:.4f}, "
            f"q_value={self.q_values[action]:.4f}, count={int(self.action_counts[action])}"
        )

    def get_best_action(self) -> int:
        """Retorna la mejor acción según Q-values actuales"""
        return int(np.argmax(self.q_values))

    def get_statistics(self) -> Dict:
        """
        Retorna estadísticas completas del bandit

        Returns:
            Dict con métricas y estado actual
        """
        total_actions = int(sum(self.action_counts))

        return {
            'q_values': self.q_values.tolist(),
            'action_counts': self.action_counts.tolist(),
            'action_probabilities': (self.action_counts / max(total_actions, 1)).tolist(),
            'total_reward': float(self.total_reward),
            'avg_reward': float(self.total_reward / max(total_actions, 1)),
            'best_action': int(self.get_best_action()),
            'best_q_value': float(np.max(self.q_values)),
            'epsilon': self.epsilon,
            'total_actions': total_actions
        }

    def save_state(self, filepath: str):
        """
        Guarda estado del bandit a archivo JSON

        Args:
            filepath: Ruta del archivo
        """
        try:
            state = {
                'n_arms': self.n_arms,
                'epsilon': self.epsilon,
                'learning_rate': self.learning_rate,
                'q_values': self.q_values.tolist(),
                'action_counts': self.action_counts.tolist(),
                'total_reward': float(self.total_reward),
                'history': self.history[-1000:],  # Guardar últimas 1000 acciones
                'last_updated': datetime.now().isoformat()
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)

            logger.info(f"Bandit state saved to {filepath}")

        except Exception as e:
            logger.error(f"Error saving bandit state: {e}")

    def load_state(self, filepath: str):
        """
        Carga estado del bandit desde archivo JSON

        Args:
            filepath: Ruta del archivo
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                state = json.load(f)

            # Restaurar estado
            self.n_arms = state.get('n_arms', self.n_arms)
            self.epsilon = state.get('epsilon', self.epsilon)
            self.learning_rate = state.get('learning_rate', self.learning_rate)
            self.q_values = np.array(state['q_values'])
            self.action_counts = np.array(state['action_counts'])
            self.total_reward = state['total_reward']
            self.history = state.get('history', [])

            logger.info(
                f"Bandit state loaded from {filepath}: "
                f"total_actions={int(sum(self.action_counts))}, "
                f"best_action={self.get_best_action()}"
            )

        except FileNotFoundError:
            logger.warning(f"State file {filepath} not found, using fresh initialization")
        except Exception as e:
            logger.error(f"Error loading bandit state: {e}")

    def reset(self):
        """Reinicia el bandit a estado inicial"""
        self.q_values = np.zeros(self.n_arms)
        self.action_counts = np.zeros(self.n_arms)
        self.total_reward = 0
        self.history = []
        logger.info("Bandit reset to initial state")
