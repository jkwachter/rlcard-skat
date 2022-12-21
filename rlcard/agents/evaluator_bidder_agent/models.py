import torch
import torch.nn as nn

class SkatEvaluatorLSTM(nn.Module):
    def __init__(self, input_size, hidden_size, output_size, num_layers=1):
        super(SkatEvaluatorLSTM, self).__init__()
        self.input_size = input_size  # size of each input feature
        self.hidden_size = hidden_size  # size of the hidden state
        self.output_size = output_size  # size of the output
        self.num_layers = num_layers  # number of LSTM layers
        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)
    
    def forward(self, x, hidden=None):
        # x shape: (batch_size, sequence_length, input_size)
        x, hidden = self.lstm(x, hidden)
        # x shape: (batch_size, sequence_length, hidden_size)
        x = self.fc(x[:, -1, :])  # take the last hidden state as output
        # x shape: (batch_size, output_size)
        return x, hidden

class SkatBidderLSTM(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(162, 128, batch_first=True)
        self.dense1 = nn.Linear(484 + 128, 512)
        self.dense2 = nn.Linear(512, 512)
        self.dense3 = nn.Linear(512, 512)
        self.dense4 = nn.Linear(512, 512)
        self.dense5 = nn.Linear(512, 512)
        self.dense6 = nn.Linear(512, 1)

    def forward(self, z, x, return_value=False, flags=None):
        lstm_out, (h_n, _) = self.lstm(z)
        lstm_out = lstm_out[:,-1,:]
        x = torch.cat([lstm_out,x], dim=-1)
        x = self.dense1(x)
        x = torch.relu(x)
        x = self.dense2(x)
        x = torch.relu(x)
        x = self.dense3(x)
        x = torch.relu(x)
        x = self.dense4(x)
        x = torch.relu(x)
        x = self.dense5(x)
        x = torch.relu(x)
        x = self.dense6(x)
        if return_value:
            return dict(values=x)
        else:
            if flags is not None and flags.exp_epsilon > 0 and np.random.rand() < flags.exp_epsilon:
                action = torch.randint(x.shape[0], (1,))[0]
            else:
                action = torch.argmax(x,dim=0)[0]
            return dict(action=action)
        
# Two main models to play the game, the evaluator and bidder agents (which have been trained on all 3 game positions [forhand, middlehand, and rearhand])
model_dict = {}
model_dict['evaluator'] = SkatEvaluatorLSTM
model_dict['bidder'] = SkatBidderLSTM

class Model:
    """
    The wrapper for the three models. We also wrap several
    interfaces such as share_memory, eval, etc.
    """
    def __init__(self, device=0):
        self.models = {}
        if not device == "cpu":
            device = 'cuda:' + str(device)
        self.models['evaluator'] = SkatEvaluatorLSTM().to(torch.device(device))
        self.models['bidder'] = SkatBidderLSTM().to(torch.device(device))

    def forward(self, position, z, x, training=False, flags=None):
        model = self.models[position]
        return model.forward(z, x, training, flags)
    
    # Share information between the two game states to create a smooth transition between the two 
    def share_memory(self):# Important to note that some memory is shared between these two models in order to allow for smooth transitions between game states (as card-playing may be dependent on bidding sizes and vice versa) between multiple rounds.
        self.models['evaluator'].share_memory()
        self.models['bidder'].share_memory()

    def eval(self):
        self.models['evaluator'].eval()
        self.models['bidder'].eval()

    def parameters(self, position):
        return self.models[position].parameters()

    def get_model(self, position):
        return self.models[position]

    def get_models(self):
        return self.models