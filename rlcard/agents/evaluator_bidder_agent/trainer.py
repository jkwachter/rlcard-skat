import torch
import torch.optim as optim

from rlcard.envs.skat import SkatEnv
from .models import SkatEvaluatorLSTM

env = SkatEnv()

evaluator_lstm = SkatEvaluatorLSTM(input_size=32, hidden_size=128, output_size=3)

optimizer = optim.Adam(evaluator_lstm.parameters())

loss_fn = torch.CrossEntropyLoss()

num_episodes = 1000
max_steps = 50

gamma = 0.99

exploration_rate = 0.1

for episode in range(num_episodes):
    state = env.reset()
    hidden = None
    
    episode_reward = 0
    
    for step in range(max_steps):
        x = torch.tensor(state['hand'], dtype=torch.float)
        x = x.view(1, 1, -1)  # reshape to (batch_size, sequence_length, input_size)
        logits, hidden = evaluator_lstm(x, hidden)
        action_probs = F.softmax(logits, dim=1)
        
        action = torch.multinomial(action_probs, num_samples=1).item()
        
        next_state, reward, done, _ = env.step(action)
        
        episode_reward += reward
        
        if done:
            target_q_value = reward
        else:
            next_x = torch.tensor(next_state['hand'], dtype=torch.float)
            next_x = next_x.view(1, 1, -1)  # reshape to (batch_size, sequence_length, input_size)
            next_logits, _ = evaluator_lstm(next_x, hidden)
            next_action_probs = F.softmax(next_logits, dim=1)
            target_q_value = reward + gamma * next_action_probs[0][action]
        
        loss = loss_fn(logits, torch.tensor([action]))