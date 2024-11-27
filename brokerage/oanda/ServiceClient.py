class ServiceClient:
    def __init__(self):
        pass

    def get_size_config(self, inst):
        order_min_contract = 1
        contract_size = 1
        return order_min_contract, contract_size

    def get_order_spec(self, inst, scaled_units, current_contracts):
        order_min_contracts, contract_size = self.get_size_config(inst)
        order_min_units = order_min_contracts * contract_size

        optimal_min_order = scaled_units / order_min_units
        rounded_min_order = round(optimal_min_order)

        return {
            "instrument": inst,
            "scaled_units": scaled_units,
            "contract_size": contract_size,
            "order_min_contracts": order_min_contracts,
            "order_min_units": order_min_units,
            "optimal_contracts": optimal_min_order * order_min_contracts,
            "rounded_contracts": rounded_min_order * order_min_contracts,
            "current_contracts": current_contracts,
            "current_units": self.contracts_to_units(inst, current_contracts),
        }

    def label_to_code_nomenclature(self, label):
        return label

    def code_to_label_nomenclature(self, code):
        return code

    def contracts_to_units(self, label, contracts):
        order_min_contracts, contract_size = self.get_size_config(label)
        return contracts * contract_size

    def units_to_contracts(self, label, units):
        order_min_contracts, contract_size = self.get_size_config(label)
        return units / contract_size

    def is_intertia_overriden(self, percentage_change):
        return percentage_change > 0.05
