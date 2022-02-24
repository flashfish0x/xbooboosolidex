import brownie
from brownie import Contract
from brownie import config
import math



def test_live(Contract, accounts, whale, wftm, GenericMasterChefStrategy, chain):
    wftm = Contract("0x21be370D5312f44cB42ce377BC9b8a0cEF1A4C83")
    masterchef = Contract("0x1315206208b69487116b1735db3D1D63dB78Df9e")
    pid = 0
    emissionToken = Contract("0x0B41469497f46efA3937fba4ed92153146F55ca9")
    
    #new_strat = Contract("0x28F2fB6730d5dbeFc4FF9eB375Bbf33BcB36e774")
    old_strat = Contract("0x28F2fB6730d5dbeFc4FF9eB375Bbf33BcB36e774")
    oldas = old_strat.estimatedTotalAssets()
    strategist = accounts.at(old_strat.strategist(), force=True)
    usdc_vault = Contract("0xEF0210eB96c7EB36AF8ed1c20306462764935607")
    wftm_vault = Contract("0x0DEC85e74A92c52b7F708c4B10207D9560CEFaf0")
    #t1 = old_strat.clone0xDAOStaker(wftm_vault, strategist, old_strat.rewards(), old_strat.keeper(),
    #    pid,
    #    "Scarface WFTM Masterchef",
    #    masterchef,
    #    emissionToken,
    #    wftm,
    #    True, {'from': strategist})

    #strategy = GenericMasterChefStrategy.at(t1.return_value)
    wftm_strategy = GenericMasterChefStrategy.at("0x82CbD2AF730D3dC3715873eA030851D7f3206Bcd")
    usdc_strategy = Contract("0x32aC76a38027C95662d727aee9D9Bb3028197ba7")
    #strategy = strategist.deploy(
    #    GenericMasterChefStrategy,
    #    wftm_vault,
    #    pid,
    #    "Printer WFTM Masterchef",
    #    masterchef,
    #    emissionToken,
    #    wftm,
    #    True
    #)
    #new_strat.setUseSpiritOne(True, {'from': strategist})

    
    gov = accounts.at(wftm_vault.governance(), force=True)
    wftm_vault.addStrategy(wftm_strategy, 100, 0, 2 ** 256 - 1, 1_000, {"from": gov})
    usdc_vault.addStrategy(usdc_strategy, 100, 0, 2 ** 256 - 1, 1_000, {"from": gov})
    #wftm_vault.migrateStrategy(old_strat, new_strat, {'from': gov})
    old_assets = wftm_vault.totalAssets()
    old_assets_usdc = usdc_vault.totalAssets()
    #print(new_strat.estimatedTotalAssets())
    #assert oldas == new_strat.estimatedTotalAssets()
    
    #emission = Contract(new_strat.emissionToken())
    #assert emission.balanceOf(new_strat) > 0
    wftm_strategy.harvest({'from': gov})
    wftm_strategy.setAutoSell(True, {'from': gov})
    usdc_strategy.harvest({'from': gov})
    usdc_strategy.setAutoSell(True, {'from': gov})
    chain.sleep(43200)
    chain.mine(1)

    #t1 = strategy.harvest({'from': strategist})
    wftm_strategy.harvest({'from': gov})
    usdc_strategy.harvest({'from': gov})
    
    wftm_token = Contract(wftm_vault.token())
    usdc_token = Contract(usdc_vault.token())

    #t1 = old_strat.clone0xDAOStaker(wftm_vault, strategist, old_strat.rewards(), old_strat.keeper(),
    #    pid,
    #    "Printer WFTM Masterchef",
    #    masterchef,
    #    emissionToken,
    #    wftm,
    #    False, {'from': strategist})
    #strategy2 = GenericMasterChefStrategy.at(t1.return_value)
    #strategy2 = strategist.deploy(
    #    GenericMasterChefStrategy,
    #    wftm_vault,
    #    pid,
    #    "Printer WFTM Masterchef",
    #    masterchef,
    #    emissionToken,
    #    wftm,
    #    True
    #)
    #wftm_vault.migrateStrategy(strategy, strategy2, {'from': gov})

    #assert emissionToken.balanceOf(strategy2) > 0
    #assert strategy2.estimatedTotalAssets() == wftm_vault.strategies(strategy2).dict()["totalDebt"]
    #strategy = strategy2

    chain.sleep(1)

    new_assets = wftm_vault.totalAssets()
    usdc_new_assets = usdc_vault.totalAssets()
    # confirm we made money, or at least that we have about the same
    assert new_assets >= old_assets
    print(
        "\wftm Vault total assets after 1 harvest: ", new_assets / (10 ** wftm_token.decimals())
    )
    print(
        "\nusdc total assets after 1 harvest: ", usdc_new_assets / (10 ** usdc_token.decimals())
    )


    # Display estimated APR
    print(
        "\nEstimated APR: ",
        "{:.2%}".format(
            ((new_assets - old_assets) * (365 * 2)) / (wftm_strategy.estimatedTotalAssets())
        ),
    )
    apr = ((new_assets - old_assets) * (365 * 2)) / (wftm_strategy.estimatedTotalAssets())
    assert apr > 0
    print(
        "\nEstimated APR: ",
        "{:.2%}".format(
            ((usdc_new_assets - old_assets_usdc) * (365 * 2)) / (usdc_strategy.estimatedTotalAssets())
        ),
    )
    apr = ((usdc_new_assets - old_assets_usdc) * (365 * 2)) / (usdc_strategy.estimatedTotalAssets())
    assert apr > 0

    wftm_vault.updateStrategyDebtRatio(wftm_strategy, 0, {'from': gov})
    usdc_vault.updateStrategyDebtRatio(usdc_strategy, 0, {'from': gov})

    wftm_strategy.emergencyWithdraw({'from': gov})
    assert wftm_strategy.estimatedTotalAssets() == wftm.balanceOf(wftm_strategy)
    wftm_strategy.harvest({'from': gov})
    assert wftm_strategy.estimatedTotalAssets() == 0
    print(wftm_vault.strategies(wftm_strategy).dict())

    usdc_strategy.emergencyWithdraw({'from': gov})
    assert usdc_strategy.estimatedTotalAssets() == usdc_token.balanceOf(usdc_strategy)
    usdc_strategy.harvest({'from': gov})
    assert usdc_strategy.estimatedTotalAssets() == 0
    print(usdc_vault.strategies(usdc_strategy).dict())