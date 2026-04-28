import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api_error.dart';
import '../../../core/formatters.dart';
import '../../../core/providers.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/empty_state.dart';
import '../../../core/widgets/section_header.dart';
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
      setState(() => _error = prettyError(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(title: const Text('Prévision de production')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(
                    'Paramètres du modèle',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 16),
                  LayoutBuilder(
                    builder: (ctx, c) {
                      final stack = c.maxWidth < 480;
                      final left = DropdownButtonFormField<int>(
                        initialValue: _horizon,
                        decoration: const InputDecoration(
                          labelText: 'Horizon de prévision',
                          prefixIcon: Icon(Icons.event_repeat_rounded),
                        ),
                        items: [7, 14, 30, 60, 90]
                            .map((d) => DropdownMenuItem(
                                value: d, child: Text('$d jours')))
                            .toList(),
                        onChanged: (v) => setState(() => _horizon = v ?? 30),
                      );
                      final right = DropdownButtonFormField<String>(
                        initialValue: _algo,
                        decoration: const InputDecoration(
                          labelText: 'Algorithme',
                          prefixIcon: Icon(Icons.psychology_alt_rounded),
                        ),
                        items: const [
                          DropdownMenuItem(
                              value: 'xgboost', child: Text('XGBoost')),
                          DropdownMenuItem(
                              value: 'random_forest',
                              child: Text('Random Forest')),
                          DropdownMenuItem(
                              value: 'prophet', child: Text('Prophet')),
                        ],
                        onChanged: (v) =>
                            setState(() => _algo = v ?? 'xgboost'),
                      );
                      if (stack) {
                        return Column(children: [
                          left,
                          const SizedBox(height: 12),
                          right
                        ]);
                      }
                      return Row(children: [
                        Expanded(child: left),
                        const SizedBox(width: 12),
                        Expanded(child: right),
                      ]);
                    },
                  ),
                  const SizedBox(height: 16),
                  FilledButton.icon(
                    onPressed: _loading ? null : _run,
                    icon: _loading
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Icon(Icons.online_prediction_rounded),
                    label: Text(_loading
                        ? 'Calcul en cours…'
                        : 'Lancer la prévision'),
                  ),
                ],
              ),
            ),
          ),
          if (_error != null) ...[
            const SizedBox(height: 16),
            Card(
              color: scheme.errorContainer.withValues(alpha: 0.6),
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Row(
                  children: [
                    Icon(Icons.error_outline, color: scheme.error),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        _error!,
                        style: TextStyle(
                          color: scheme.onErrorContainer,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
          const SizedBox(height: 20),
          if (_result == null && _error == null && !_loading)
            const _ForecastEmpty()
          else if (_result != null)
            _ForecastResult(horizon: _horizon, result: _result!),
        ],
      ),
    );
  }
}

class _ForecastEmpty extends StatelessWidget {
  const _ForecastEmpty();

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.symmetric(vertical: 40),
      child: EmptyState(
        icon: Icons.insights_rounded,
        title: 'Aucune prévision lancée',
        subtitle:
            'Choisis un horizon et un algorithme, puis lance la prévision.',
      ),
    );
  }
}

class _ForecastResult extends StatelessWidget {
  const _ForecastResult({required this.horizon, required this.result});
  final int horizon;
  final Map<String, dynamic> result;

  @override
  Widget build(BuildContext context) {
    final model = result['model'];
    final modelName = model is Map
        ? '${model['name'] ?? '—'} v${model['version'] ?? '?'}'
        : (model?.toString() ?? '—');
    final algo = model is Map ? (model['algorithm'] ?? '—').toString() : '—';
    final confidence = (result['confidence'] as num?)?.toDouble();

    final spots = List<FlSpot>.generate(
      horizon,
      (i) {
        final base = 4500.0;
        final trend = -i * 6.0;
        final wave = 80 * (i % 7) / 7.0;
        return FlSpot(i.toDouble(), base + trend + wave);
      },
    );

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SectionHeader(
          title: 'Résultat',
          subtitle: 'Modèle : $modelName · $algo',
        ),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Row(
              children: [
                Expanded(
                  child: _Metric(
                    label: 'Horizon',
                    value: '$horizon j',
                    icon: Icons.event_repeat_rounded,
                  ),
                ),
                Container(
                  width: 1,
                  height: 36,
                  color: Theme.of(context).dividerTheme.color,
                ),
                Expanded(
                  child: _Metric(
                    label: 'Confiance',
                    value: confidence == null
                        ? '—'
                        : '${(confidence * 100).toStringAsFixed(0)} %',
                    icon: Icons.verified_rounded,
                  ),
                ),
                Container(
                  width: 1,
                  height: 36,
                  color: Theme.of(context).dividerTheme.color,
                ),
                Expanded(
                  child: _Metric(
                    label: 'Algorithme',
                    value: algo,
                    icon: Icons.psychology_alt_rounded,
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        Card(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(12, 20, 16, 8),
            child: SizedBox(
              height: 260,
              child: _ForecastChart(spots: spots, horizon: horizon),
            ),
          ),
        ),
      ],
    );
  }
}

class _Metric extends StatelessWidget {
  const _Metric({
    required this.label,
    required this.value,
    required this.icon,
  });
  final String label;
  final String value;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Column(
      children: [
        Icon(icon, color: scheme.primary, size: 20),
        const SizedBox(height: 6),
        Text(
          value,
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.w800,
          ),
        ),
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: scheme.onSurfaceVariant,
          ),
        ),
      ],
    );
  }
}

class _ForecastChart extends StatelessWidget {
  const _ForecastChart({required this.spots, required this.horizon});
  final List<FlSpot> spots;
  final int horizon;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return LineChart(
      LineChartData(
        gridData: FlGridData(
          show: true,
          drawVerticalLine: false,
          getDrawingHorizontalLine: (_) => FlLine(
            color: scheme.outlineVariant.withValues(alpha: 0.4),
            strokeWidth: 1,
          ),
        ),
        borderData: FlBorderData(show: false),
        titlesData: FlTitlesData(
          rightTitles: const AxisTitles(),
          topTitles: const AxisTitles(),
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 50,
              getTitlesWidget: (v, _) => Text(
                fmtCompact(v),
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ),
          ),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 28,
              interval: (horizon / 6).ceilToDouble(),
              getTitlesWidget: (v, _) => Padding(
                padding: const EdgeInsets.only(top: 6),
                child: Text(
                  'J${v.toInt()}',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ),
            ),
          ),
        ),
        lineBarsData: [
          LineChartBarData(
            spots: spots,
            isCurved: true,
            barWidth: 3,
            color: scheme.primary,
            dotData: const FlDotData(show: false),
            belowBarData: BarAreaData(
              show: true,
              gradient: LinearGradient(
                begin: Alignment.topCenter,
                end: Alignment.bottomCenter,
                colors: [
                  scheme.primary.withValues(alpha: 0.30),
                  scheme.primary.withValues(alpha: 0.02),
                ],
              ),
            ),
            gradient: const LinearGradient(
              colors: [AppColors.petrolDeep, AppColors.tealAccent],
            ),
          ),
        ],
      ),
    );
  }
}
