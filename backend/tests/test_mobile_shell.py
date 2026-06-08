import json
import subprocess
from pathlib import Path


def test_mobile_shell_declares_expo_typescript_start_script() -> None:
    mobile_path = Path(__file__).resolve().parents[2] / "mobile"

    package_json = json.loads((mobile_path / "package.json").read_text())

    assert package_json["scripts"]["start"] == "expo start"
    assert "expo" in package_json["dependencies"]
    assert "typescript" in package_json["devDependencies"]
    assert (mobile_path / "App.tsx").exists()
    assert (mobile_path / "app.json").exists()


def test_mobile_config_does_not_point_physical_devices_at_localhost() -> None:
    app_json = json.loads(
        (Path(__file__).resolve().parents[2] / "mobile" / "app.json").read_text()
    )

    assert "localhost" not in json.dumps(app_json)


def test_mobile_api_derives_backend_url_from_expo_dev_server_when_env_is_missing() -> None:
    stocks_api = (
        Path(__file__).resolve().parents[2] / "mobile" / "src" / "api" / "stocks.ts"
    ).read_text()

    assert "NativeModules.SourceCode?.scriptURL" in stocks_api
    assert "http://${host}:8000" in stocks_api
    assert '?? "http://localhost:8000"' not in stocks_api


def test_mobile_declares_forecast_horizon_preference_storage() -> None:
    storage_path = (
        Path(__file__).resolve().parents[2]
        / "mobile"
        / "src"
        / "storage"
        / "forecastHorizon.ts"
    )

    source = storage_path.read_text()

    assert 'const FORECAST_HORIZON_KEY = "trendwise.forecastHorizon"' in source
    assert 'export const DEFAULT_FORECAST_HORIZON: ForecastHorizon = "1d"' in source
    assert '"30m", "1d", "5d", "7d", "1mo", "6mo", "1y"' in source
    assert "FORECAST_HORIZON_LABELS" in source
    assert '"1mo": "1 month"' in source
    assert "loadForecastHorizon" in source
    assert "saveForecastHorizon" in source


def test_mobile_forecast_horizon_storage_rejects_ambiguous_values() -> None:
    source = (
        Path(__file__).resolve().parents[2]
        / "mobile"
        / "src"
        / "storage"
        / "forecastHorizon.ts"
    ).read_text()

    assert 'return DEFAULT_FORECAST_HORIZON' in source
    assert 'value is ForecastHorizon' in source
    assert '"1M"' not in source
    assert '"30M"' not in source
    assert '"2d"' not in source


def test_mobile_forecast_horizon_storage_persists_only_canonical_values(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    mobile_path = repo_root / "mobile"
    source_path = mobile_path / "src" / "storage" / "forecastHorizon.ts"
    temp_src_path = tmp_path / "src" / "storage" / "forecastHorizon.ts"
    async_storage_path = (
        tmp_path
        / "node_modules"
        / "@react-native-async-storage"
        / "async-storage"
    )

    temp_src_path.parent.mkdir(parents=True)
    temp_src_path.write_text(source_path.read_text())
    (tmp_path / "src" / "api").mkdir(parents=True)
    (tmp_path / "src" / "api" / "stocks.ts").write_text(
        "export type ForecastHorizon = "
        "'30m' | '1d' | '5d' | '7d' | '1mo' | '6mo' | '1y';\n"
    )
    async_storage_path.mkdir(parents=True)
    (async_storage_path / "index.d.ts").write_text(
        "declare const AsyncStorage: {\n"
        "  getItem(key: string): Promise<string | null>;\n"
        "  setItem(key: string, value: string): Promise<void>;\n"
        "};\n"
        "export default AsyncStorage;\n"
    )
    (async_storage_path / "index.js").write_text(
        "const store = new Map();\n"
        "module.exports = {\n"
        "  __store: store,\n"
        "  getItem: async (key) => store.has(key) ? store.get(key) : null,\n"
        "  setItem: async (key, value) => { store.set(key, value); },\n"
        "};\n"
    )
    (tmp_path / "forecastHorizonBehavior.test.ts").write_text(
        "declare const require: (name: string) => {\n"
        "  equal(actual: unknown, expected: unknown): void;\n"
        "};\n"
        "declare const process: { exit(code: number): never };\n"
        "const assert = require('node:assert/strict');\n"
        "import AsyncStorage from '@react-native-async-storage/async-storage';\n"
        "import {\n"
        "  loadForecastHorizon,\n"
        "  saveForecastHorizon,\n"
        "} from './src/storage/forecastHorizon';\n"
        "\n"
        "const store = (AsyncStorage as unknown as { __store: Map<string, string> })"
        ".__store;\n"
        "const key = 'trendwise.forecastHorizon';\n"
        "\n"
        "async function run() {\n"
        "  store.clear();\n"
        "  assert.equal(await loadForecastHorizon(), '1d');\n"
        "\n"
        "  store.set(key, '{not json');\n"
        "  assert.equal(await loadForecastHorizon(), '1d');\n"
        "\n"
        "  for (const unsupported of ['1M', '30M', '2d']) {\n"
        "    store.set(key, JSON.stringify(unsupported));\n"
        "    assert.equal(await loadForecastHorizon(), '1d');\n"
        "  }\n"
        "\n"
        "  store.clear();\n"
        "  await saveForecastHorizon('1mo');\n"
        "  assert.equal(store.get(key), JSON.stringify('1mo'));\n"
        "  assert.equal(await loadForecastHorizon(), '1mo');\n"
        "}\n"
        "\n"
        "run().catch((error) => {\n"
        "  console.error(error);\n"
        "  process.exit(1);\n"
        "});\n"
    )
    (tmp_path / "tsconfig.json").write_text(
        json.dumps(
            {
                "compilerOptions": {
                    "module": "commonjs",
                    "target": "es2020",
                    "moduleResolution": "node",
                    "ignoreDeprecations": "6.0",
                    "strict": True,
                    "esModuleInterop": True,
                    "skipLibCheck": True,
                    "outDir": "dist",
                },
                "include": ["forecastHorizonBehavior.test.ts", "src/**/*.ts"],
            }
        )
    )

    subprocess.run(
        [str(mobile_path / "node_modules" / ".bin" / "tsc"), "-p", str(tmp_path)],
        check=True,
        cwd=tmp_path,
    )
    subprocess.run(
        ["node", str(tmp_path / "dist" / "forecastHorizonBehavior.test.js")],
        check=True,
        cwd=tmp_path,
    )


def test_mobile_app_loads_and_saves_selected_forecast_horizon() -> None:
    app_source = (Path(__file__).resolve().parents[2] / "mobile" / "App.tsx").read_text()

    assert "loadForecastHorizon" in app_source
    assert "saveForecastHorizon" in app_source
    assert "selectedHorizon" in app_source
    assert "handleChangeHorizon" in app_source
    assert "getStockDetail(stock.ticker, horizon)" in app_source
    assert 'getStockDetail(stock.ticker, "1d")' not in app_source


def test_mobile_app_keeps_current_detail_visible_when_horizon_reload_fails() -> None:
    app_source = (Path(__file__).resolve().parents[2] / "mobile" / "App.tsx").read_text()

    assert "fallbackDetail?: StockDetail" in app_source
    assert 'setAppState({ status: "detail", stock, detail: fallbackDetail })' in app_source
    assert "loadDetailForStock(currentState.stock, horizon, currentState.detail)" in app_source


def test_mobile_app_reloads_horizon_from_captured_state_before_async_save() -> None:
    app_source = (Path(__file__).resolve().parents[2] / "mobile" / "App.tsx").read_text()
    handle_source = app_source.split("async function handleChangeHorizon", 1)[1].split(
        "async function handleChangeStock", 1
    )[0]

    capture_index = handle_source.index("const currentState = appState;")
    reload_index = handle_source.index("loadDetailForStock(currentState.stock, horizon")
    save_index = handle_source.index("await savePromise;")

    assert capture_index < reload_index < save_index
    assert "loadDetailForStock(appState.stock, horizon" not in handle_source


def test_mobile_stock_detail_exposes_forecast_horizon_selector() -> None:
    detail_source = (
        Path(__file__).resolve().parents[2]
        / "mobile"
        / "src"
        / "screens"
        / "StockDetailScreen.tsx"
    ).read_text()

    assert "selectedHorizon" in detail_source
    assert "horizonOptions" in detail_source
    assert "onChangeHorizon" in detail_source
    assert "Forecast horizon" in detail_source
    assert "accessibilityLabel={`Select ${option.label} Forecast Horizon`}" in detail_source
    assert "accessibilityState={{ selected: isSelected }}" in detail_source
    assert "minHeight: 44" in detail_source
    assert "minWidth: 44" in detail_source
    assert 'alignItems: "center"' in detail_source
    assert 'justifyContent: "center"' in detail_source


def test_mobile_declares_graph_type_preference_storage() -> None:
    storage_path = (
        Path(__file__).resolve().parents[2]
        / "mobile"
        / "src"
        / "storage"
        / "graphType.ts"
    )

    source = storage_path.read_text()

    assert 'const GRAPH_TYPE_KEY = "trendwise.graphType"' in source
    assert 'export type GraphType = "line" | "candlestick"' in source
    assert 'export const DEFAULT_GRAPH_TYPE: GraphType = "line"' in source
    assert 'export const GRAPH_TYPES: GraphType[] = ["line", "candlestick"]' in source
    assert "value is GraphType" in source
    assert "loadGraphType" in source
    assert "saveGraphType" in source
    load_source = source.split("export async function loadGraphType", 1)[1].split(
        "export async function saveGraphType",
        1,
    )[0]
    assert load_source.index("try {") < load_source.index("AsyncStorage.getItem")
    assert "catch" in load_source
    assert "return DEFAULT_GRAPH_TYPE" in load_source


def test_mobile_app_loads_and_saves_selected_graph_type() -> None:
    app_source = (Path(__file__).resolve().parents[2] / "mobile" / "App.tsx").read_text()

    assert "loadGraphType" in app_source
    assert "saveGraphType" in app_source
    assert "selectedGraphType" in app_source
    assert "handleChangeGraphType" in app_source
    assert "saveGraphTypeQueue" in app_source
    assert "onChangeGraphType={handleChangeGraphType}" in app_source
    assert "selectedGraphType={selectedGraphType}" in app_source
