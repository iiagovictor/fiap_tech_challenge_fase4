import matplotlib.dates as mdates


def preencher_nulos(df, colunas, valor_preenchimento):
    df_copia = df.copy()
    df_copia[colunas] = df_copia[colunas].fillna(valor_preenchimento)

    return df_copia


def formatar_eixo_ano(ax):
    """Ajusta o eixo X para mostrar apenas o ano de forma limpa."""
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    return ax
