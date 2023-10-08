import numpy as np

class QLearning:
    def __init__(self, actions, alpha=0.1, gamma=0.95, epsilon=0.1):
        self.q_table = {}
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.actions = actions

    def get_q(self, state, action):
        return self.q_table.get((state, action), 0.0)

    def choose_action(self, state):
        if np.random.uniform(0, 1) < self.epsilon:
            return np.random.choice(self.actions)
        q_values = [self.get_q(state, action) for action in self.actions]
        return self.actions[np.argmax(q_values)]

    def learn(self, state, action, reward, next_state):
        old_q_value = self.get_q(state, action)
        max_future_q = max([self.get_q(next_state, a) for a in self.actions])
        new_q_value = (1 - self.alpha) * old_q_value + self.alpha * (reward + self.gamma * max_future_q)
        self.q_table[(state, action)] = new_q_value

