import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.layers import Input, LSTM, Dense, Dropout
from tensorflow.keras.models import Model
import matplotlib.pyplot as plt
import mplcursors  # To enable the cursor interaction

# Load the data from CSV (for Tesla)
data = pd.read_csv('C:/Users/legen/OneDrive/YG/Excel/STCOKDATA/TESLA.csv')  # Update with Tesla stock data file path
data = data[['Date', 'Close']]  # Assuming 'Close' price is the target
data['Date'] = pd.to_datetime(data['Date'])
data.set_index('Date', inplace=True)

# Scale the data
scaler = MinMaxScaler(feature_range=(0, 1))
scaled_data = scaler.fit_transform(data['Close'].values.reshape(-1, 1))

# Define a Flexible Time Step
time_step = 60  # Time steps for sequence creation
if len(scaled_data) < time_step:
    print(f"Dataset has only {len(scaled_data)} data points, reducing time_step.")
    time_step = len(scaled_data) - 1
    if time_step < 1:
        raise ValueError(f"Dataset is too small for the time_step. Please use a larger dataset.")
else:
    if len(scaled_data) < 2 * time_step:
        time_step = len(scaled_data) // 2
        print(f"Reducing time_step to {time_step} due to small dataset size.")

# Create Sequences for LSTM
def create_sequences(data, time_step=60):
    X, y = [], []
    for i in range(time_step, len(data)):
        X.append(data[i - time_step:i, 0])
        y.append(data[i, 0])
    return np.array(X), np.array(y)

X, y = create_sequences(scaled_data, time_step)

X = np.reshape(X, (X.shape[0], X.shape[1], 1))

# Split the data into training and testing sets
train_size = int(len(X) * 0.8)
X_train, X_test = X[:train_size], X[train_size:]
y_train, y_test = y[:train_size], y[train_size:]

# Build the LSTM Model
input_layer = Input(shape=(X_train.shape[1], 1))  # Define input layer
lstm_layer1 = LSTM(50, return_sequences=True)(input_layer)
dropout_layer1 = Dropout(0.2)(lstm_layer1)
lstm_layer2 = LSTM(50, return_sequences=True)(dropout_layer1)
dropout_layer2 = Dropout(0.2)(lstm_layer2)
lstm_layer3 = LSTM(50)(dropout_layer2)
dropout_layer3 = Dropout(0.2)(lstm_layer3)
output_layer = Dense(1)(dropout_layer3)

# Define the model
model = Model(inputs=input_layer, outputs=output_layer)

# Compile the model
model.compile(optimizer='adam', loss='mean_squared_error')

# Train the Model
model.fit(X_train, y_train, epochs=100, batch_size=32, validation_data=(X_test, y_test))

# Make Predictions on the test data
predicted_prices = model.predict(X_test)
predicted_prices = scaler.inverse_transform(predicted_prices)  # Reverse scaling

# Get the real stock prices for the test data
real_prices = scaler.inverse_transform(y_test.reshape(-1, 1))

# Plot the results
plt.figure(figsize=(14, 5))
plt.plot(real_prices, color='black', label='Historical Stock Price')
plt.plot(predicted_prices, color='blue', label='Predicted Stock Price')

# Ensure the length is large enough for monthly ticks (at least 12 data points)
total_points = len(real_prices)
num_ticks = min(12, total_points)
tick_step = max(total_points // num_ticks, 1)
month_labels = [f'Month {i+1}' for i in range(min(num_ticks, total_points))]
plt.xticks(ticks=np.arange(0, total_points, tick_step), labels=month_labels)

# Format the y-axis with dollar sign
plt.gca().yaxis.set_major_formatter(plt.matplotlib.ticker.FuncFormatter(lambda x, _: f'${x:.2f}'))

# Add interactive hover functionality (show price only)
mplcursors.cursor(hover=True).connect("add", lambda sel: sel.annotation.set_text(
    f'Price: ${sel.target[1]:.2f}'))

plt.xlabel('Time (Months)')
plt.ylabel('Stock Price (USD)')
plt.title('Tesla Stock Price Prediction\nLSTM Model Results')
plt.legend()
plt.show()

# Future prediction for the next 6 months
last_60_days = scaled_data[-time_step:]  # Take the last 60 days of the dataset
predicted_future_prices = []

for _ in range(6):  # Predict for 6 months
    last_60_days_reshaped = last_60_days.reshape(1, time_step, 1)
    future_price = model.predict(last_60_days_reshaped)
    predicted_future_prices.append(future_price[0, 0])
    
    last_60_days = np.append(last_60_days[1:], future_price, axis=0)

# Reverse scaling to get the actual predicted prices in original scale
predicted_future_prices = scaler.inverse_transform(np.array(predicted_future_prices).reshape(-1, 1))

# Plotting the future predictions
future_dates = pd.date_range(data.index[-1], periods=7, freq='M')  # Next 6 months
plt.figure(figsize=(14, 5))
plt.plot(data.index, scaler.inverse_transform(scaled_data), color='black', label='Historical Stock Price')
plt.plot(future_dates, predicted_future_prices, color='red', label='Predicted Future Price')

# Format the y-axis with dollar sign
plt.gca().yaxis.set_major_formatter(plt.matplotlib.ticker.FuncFormatter(lambda x, _: f'${x:.2f}'))

# Add interactive hover functionality (show price only)
mplcursors.cursor(hover=True).connect("add", lambda sel: sel.annotation.set_text(
    f'Price: ${sel.target[1]:.2f}'))

plt.xlabel('Time (Months)')
plt.ylabel('Stock Price (USD)')
plt.title('Tesla Stock Price Prediction\nFuture 6 Months Forecast')
plt.legend()
plt.show()
