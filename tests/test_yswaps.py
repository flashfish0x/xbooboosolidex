import brownie
from brownie import Contract
import time
import web3
from eth_abi import encode_single, encode_abi
from brownie.convert import to_bytes
from eth_abi.packed import encode_abi_packed
import eth_utils


def test_yswap(
    gov,
    liveBooStrat,
    wftm,
    amount,
    Contract,
    ymechs_safe,
    chain,
    accounts,
    interface,
    spooky_router,
    trade_factory,
    sex,
    solid,
    multicall_swapper,
):
    strategy = liveBooStrat
    vault = Contract(strategy.vault())
    token = Contract(vault.token())
    trade_factory = Contract('0xcCF3a9d634C70cFB61e7618DA1E3b55Bb8D41945')

    print(token)
    print("CallOnlyOptimizationRequired(): ", eth_utils.to_hex(
        eth_utils.function_signature_to_4byte_selector("CallOnlyOptimizationRequired()")))
    print("InvalidSwapper(): ", eth_utils.to_hex(
        eth_utils.function_signature_to_4byte_selector("InvalidSwapper()")))
    print("SwapperInUse(): ", eth_utils.to_hex(
        eth_utils.function_signature_to_4byte_selector("SwapperInUse()")))
    print("NotAsyncSwapper(): ", eth_utils.to_hex(
        eth_utils.function_signature_to_4byte_selector("NotAsyncSwapper()")))
    print("MultiCallRevert(): ", eth_utils.to_hex(
        eth_utils.function_signature_to_4byte_selector("MultiCallRevert()")))
    print("ZeroAddress(): ", eth_utils.to_hex(
        eth_utils.function_signature_to_4byte_selector("ZeroAddress()")))
    print("NotAuthorized(): ", eth_utils.to_hex(
        eth_utils.function_signature_to_4byte_selector("NotAuthorized()")))
    print("IncorrectSwapInformation(): ", eth_utils.to_hex(
        eth_utils.function_signature_to_4byte_selector("IncorrectSwapInformation()")))
    print("ZeroSlippage(): ", eth_utils.to_hex(
        eth_utils.function_signature_to_4byte_selector("ZeroSlippage()")))

    # prob needs changing a lot
    strategist = accounts.at(strategy.strategist(), force=True)

    gov = accounts.at(vault.governance(), force=True)
    trade_factory.grantRole(
        trade_factory.STRATEGY(), strategy, {
            "from": ymechs_safe, "gas_price": "0 gwei"}
    )
    trade_factory.addSwappers([multicall_swapper], {"from": ymechs_safe})
    strategy.updateTradeFactory(trade_factory, {'from': gov})

    vault_before = token.balanceOf(vault)
    strat_before = token.balanceOf(strategy)

    strategy.harvest({"from": strategist})

    token_out = token

    ins = [solid]

    print(f"Executing trades...")
    for id in ins:

        print(id.address)
        receiver = strategy.address
        token_in = id

        amount_in = id.balanceOf(strategy)
        print(
            f"Executing trade {id}, tokenIn: {token_in} -> tokenOut {token_out} amount {amount_in/1e18}")

        asyncTradeExecutionDetails = [
            strategy, token_in, token_out, amount_in, 1]

        # always start with optimisations. 5 is CallOnlyNoValue
        optimsations = [["uint8"], [5]]
        a = optimsations[0]
        b = optimsations[1]

        calldata = token_in.approve.encode_input(spooky_router, amount_in)
        t = createTx(token_in, calldata)
        a = a + t[0]
        b = b + t[1]

        path = [token_in.address, wftm, token_out.address]
        calldata = spooky_router.swapExactTokensForTokens.encode_input(
            amount_in, 0, path, receiver, 2 ** 256 - 1
        )
        t = createTx(spooky_router, calldata)
        a = a + t[0]
        b = b + t[1]
        transaction = encode_abi_packed(a, b)

        # min out must be at least 1 to ensure that the tx works correctly
        # trade_factory.execute["uint256, address, uint, bytes"](
        #    multicall_swapper.address, 1, transaction, {"from": ymechs_safe}
        # )
        trade_factory.execute['tuple,address,bytes'](asyncTradeExecutionDetails,
                                                     multicall_swapper.address, transaction, {
                                                         "from": ymechs_safe}
                                                     )
        print(token_out.balanceOf(strategy)/1e18)
    strategy.setDoHealthCheck(False, {"from": gov})
    tx = strategy.harvest({"from": strategist})
    print('profit: ', tx.events["Harvested"]["profit"]/1e18)
    assert tx.events["Harvested"]["profit"] > 0

    #print("apr = ", (365*2*tx.events["Harvested"]["profit"]) / vault_after)


def createTx(to, data):
    inBytes = eth_utils.to_bytes(hexstr=data)
    return [["address", "uint256", "bytes"], [to.address, len(inBytes), inBytes]]
