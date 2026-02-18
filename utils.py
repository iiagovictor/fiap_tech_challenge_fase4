import matplotlib.dates as mdates
import numpy as np
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout, Input
import tensorflow as tf


def preencher_nulos(df, colunas, valor_preenchimento):
    df_copia = df.copy()
    df_copia[colunas] = df_copia[colunas].fillna(valor_preenchimento)

    return df_copia


def formatar_eixo_ano(ax):
    """Ajusta o eixo X para mostrar apenas o ano de forma limpa."""
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    return ax


def criar_sequencias(data, window_size):
    X = []
    y = []
    for i in range(len(data) - window_size):
        X.append(data[i : (i + window_size), :])  # noqa: E203
        y.append(data[i + window_size, 0])
    return np.array(X), np.array(y)


def construcao_modelo(hp):
    model = Sequential()
    model.add(Input(shape=(15, 2)))  # estrutura multivariada

    # Tunando o número de neurônios da 1ª camada (32 a 128)
    hp_units_1 = hp.Int("units_l1", min_value=32, max_value=128, step=32)
    model.add(LSTM(units=hp_units_1, return_sequences=True))
    model.add(Dropout(0.2))

    # Tunando o número de neurônios da 2ª camada
    hp_units_2 = hp.Int("units_l2", min_value=32, max_value=128, step=32)
    model.add(LSTM(units=hp_units_2, return_sequences=False))
    model.add(Dropout(0.2))

    # camada densa intermediária
    model.add(Dense(25, activation="relu"))
    model.add(Dense(1))

    # Tunando a Learning Rate
    hp_lr = hp.Choice("learning_rate", values=[1e-2, 1e-3, 1e-4])

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=hp_lr),
        loss="Huber",  # Solução que funcionou para o erro
        metrics=["mae", "mse"],
    )
    return model
