import matplotlib.dates as mdates  # Manipulação de formatos de data
import numpy as np  # Operações matemáticas e vetoriais
import tensorflow as tf  # Backend para processamento de tensores
from keras.models import Sequential  # Modelo linear de camadas
from keras.layers import LSTM, Dense, Dropout, Input  # Camadas da rede


def preencher_nulos(df, colunas, valor_preenchimento):
    """Preenche valores ausentes em colunas específicas do DataFrame."""
    df_copia = df.copy()
    df_copia[colunas] = df_copia[colunas].fillna(valor_preenchimento)
    return df_copia


def formatar_eixo_ano(ax):
    """Ajusta o eixo X para exibir apenas o ano nos gráficos."""
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    return ax


def criar_sequencias(data, window_size):
    """Gera janelas deslizantes para entrada e alvo da LSTM."""
    X = []
    y = []
    for i in range(len(data) - window_size):
        # Janela multivariada com preço e variação
        X.append(data[i : (i + window_size), :])  # noqa: E203
        # O alvo é a primeira coluna (Preço) do próximo passo
        y.append(data[i + window_size, 0])
    return np.array(X), np.array(y)


def construcao_modelo(hp):
    """Define a arquitetura otimizada via Keras Tuner."""
    model = Sequential()
    # Entrada de 15 passos temporais e 2 features
    model.add(Input(shape=(15, 2)))

    # Tunagem da 1ª camada LSTM (32 a 128 neurônios)
    hp_units_1 = hp.Int("units_l1", min_value=32, max_value=128, step=32)
    model.add(LSTM(units=hp_units_1, return_sequences=True))
    model.add(Dropout(0.2))

    # Tunagem da 2ª camada LSTM (32 a 128 neurônios)
    hp_units_2 = hp.Int("units_l2", min_value=32, max_value=128, step=32)
    model.add(LSTM(units=hp_units_2, return_sequences=False))
    model.add(Dropout(0.2))

    # Camada densa intermediária e saída única (preço previsto)
    model.add(Dense(25, activation="relu"))
    model.add(Dense(1))

    # Tunagem da taxa de aprendizado para o otimizador Adam
    hp_lr = hp.Choice("learning_rate", values=[1e-2, 1e-3, 1e-4])

    # Compilação com Huber Loss para robustez contra outliers
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=hp_lr),
        loss="Huber",
        metrics=["mae", "mse"],
    )
    return model
