import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
import '../data/forecast_repository.dart';

final _repoProvider = Provider<ForecastRepository>(
  (ref) => ForecastRepository(ref.watch(apiClientProvider)),
);

class ForecastScreen extends ConsumerStatefulWidget {
  const ForecastScreen({super.key});

  @override
  ConsumerState<ForecastScreen> createState() => _ForecastScreenState();
}

class _ForecastScreenState extends ConsumerState<ForecastScreen> {
  int _horizon = 30;
  String _algo = 'xgboost';
  Map<String, dynamic>? _result;
  bool _loading = false;
  String? _error;

  Future<void> _run() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final r = await ref
          .read(_repoProvider)
          .predictForecast(horizonDays: _horizon, algorithm: _algo);
      setState(() => _result = r);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Prévision de production')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(children: [
              Expanded(
                child: DropdownButtonFormField<int>(
                  initialValue: _horizon,
                  decoration: const InputDecoration(labelText: 'Horizon'),
                  items: [7, 14, 30, 60, 90]
                      .map((d) => DropdownMenuItem(
                          value: d, child: Text('$d jours')))
                      .toList(),
                  onChanged: (v) => setState(() => _horizon = v ?? 30),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: DropdownButtonFormField<String>(
                  initialValue: _algo,
                  decoration: const InputDecoration(labelText: 'Algorithme'),
                  items: const [
                    DropdownMenuItem(value: 'xgboost', child: Text('XGBoost')),
                    DropdownMenuItem(value: 'random_forest', child: Text('Random Forest')),
                    DropdownMenuItem(value: 'prophet', child: Text('Prophet')),
                  ],
                  onChanged: (v) => setState(() => _algo = v ?? 'xgboost'),
                ),
              ),
            ]),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: _loading ? null : _run,
              icon: _loading
                  ? const SizedBox(
                      width: 16, height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.online_prediction),
              label: const Text('Lancer la prévision'),
            ),
            const SizedBox(height: 16),
            if (_error != null)
              Text(_error!, style: const TextStyle(color: Colors.red)),
            if (_result != null) ...[
              Text('Modèle : ${_result!["model"]}'),
              const SizedBox(height: 16),
              SizedBox(
                height: 240,
                child: LineChart(LineChartData(
                  lineBarsData: [
                    LineChartBarData(
                      spots: List.generate(_horizon,
                          (i) => FlSpot(i.toDouble(), (i % 5 + 3).toDouble())),
                      isCurved: true,
                    ),
                  ],
                )),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
