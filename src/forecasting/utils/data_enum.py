from enum import Enum, auto

# new entries
# 'Energia total de compra sistema español (MWh)': [DataTypeInMarginalPriceFile.ENERGY_PURCHASE_SPAIN, 1.0],
# 'Energia total de venta sistema español (MWh)': [DataTypeInMarginalPriceFile.ENERGY_SALE_SPAIN, 1.0],
# 'Energia total de compra sistema portugués (MWh)': [DataTypeInMarginalPriceFile.ENERGY_PURCHASE_PORTUGAL, 1.0],
# 'Energia total de venta sistema português (MWh)': [DataTypeInMarginalPriceFile.ENERGY_SALE_PORTUGAL, 1.0],
# 'Importación de España desde Portugal (MWh)': [DataTypeInMarginalPriceFile.IMPORT_ES_FROM_PT, 1.0],
# 'Exportación de España a Portugal (MWh)': [DataTypeInMarginalPriceFile.EXPORT_ES_TO_PT, 1.0],
# 'Importación de España desde Portugal (MW)': [DataTypeInMarginalPriceFile.IMPORT_ES_FROM_PT, 1.0],}

class DataTypeInMarginalPriceFile(Enum):

    PRICE_SPAIN = auto()
    PRICE_PORTUGAL = auto()
    ENERGY_IBERIAN = auto()
    ENERGY_IBERIAN_WITH_BILLATERAL = auto()
    ENERGY_PURCHASE_SPAIN = auto()
    ENERGY_SALE_SPAIN = auto()
    ENERGY_PURCHASE_PORTUGAL = auto()
    ENERGY_SALE_PORTUGAL = auto()
    IMPORT_ES_FROM_PT = auto()
    EXPORT_ES_TO_PT = auto()

    __dict_concept_str__ = {PRICE_SPAIN: 'PRICE_SP',
                            PRICE_PORTUGAL: 'PRICE_PT',
                            ENERGY_IBERIAN: 'ENER_IB',
                            ENERGY_IBERIAN_WITH_BILLATERAL: 'ENER_IB_BILLAT',
                            ENERGY_PURCHASE_SPAIN: 'ENER_PURCH_SP',
                            ENERGY_SALE_SPAIN: 'ENER_SALE_SP',
                            ENERGY_PURCHASE_PORTUGAL: 'ENER_PURCH_PT',
                            ENERGY_SALE_PORTUGAL: 'ENER_SALE_PT',
                            IMPORT_ES_FROM_PT: 'IMPORT_SP_FROM_PT',
                            EXPORT_ES_TO_PT: 'EXPORT_SP_TO_PT'}

    def __str__(self):
        return self.__dict_concept_str__[self.value]