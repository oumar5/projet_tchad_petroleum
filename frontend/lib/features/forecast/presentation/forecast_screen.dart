import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/api_error.dart';
import '../../../core/formatters.dart';
import '../../../core/providers.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/empty_state.dart';
import '../../../core/widgets/kpi_card.dart';
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
  String _algo = 'gradient_boosting';
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
                              value: 'gradient_boosting',
                              child: Text('Gradient Boosting')),
                          DropdownMenuItem(
                              value: 'random_forest',
                              child: Text('Random Forest')),
                          DropdownMenuItem(
                              value: 'xgboost', child: Text('XGBoost')),
                        ],
                        onChanged: (v) =>
                            setState(() => _algo = v ?? 'gradient_boosting'),
                      );
                      if (stack) {
                        return Column(children: [
                          left,
                          const SizedBox(height: 12),
                          right,
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
            _ForecastResult(result: _result!),
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
  const _ForecastResult({required this.result});
  final Map<String, dynamic> result;

  @override
  Widget build(BuildContext context) {
    final preds = (result['predictions'] as List?) ?? const [];
    if (preds.isEmpty) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 40),
        child: EmptyState(
          icon: Icons.warning_amber_rounded,
          title: 'Le modèle n\'a renvoyé aucun point',
          subtitle: 'Vérifie qu\'un modèle de type "forecast" est entraîné.',
        ),
      );
    }
    final points = preds
        .map((p) => Map<String, dynamic>.from(p as Map))
        .toList(growable: false);

    final values = points
        .map((p) => (p['predicted_oil_bbl'] as num?)?.toDouble() ?? 0)
        .toList();
    final total = values.fold<double>(0, (a, b) => a + b);
    final avg = values.isEmpty ? 0.0 : total / values.length;
    final peak = values.isEmpty
        ? 0.0
        : values.reduce((a, b) => a > b ? a : b);
    final low = values.isEmpty
        ? 0.0
        : values.reduce((a, b) => a < b ? a : b);
    final firstVal = values.first;
    final lastVal = values.last;
    final trendPct = firstVal == 0 ? 0.0 : ((lastVal - firstVal) / firstVal) * 100;

    final model = Map<String, dynamic>.from(result['model'] as Map);
    final modelName = '${model['name']} ${model['version']}';
    final algo = model['algorithm']?.toString() ?? '—';
    final confidence = (result['confidence'] as num?)?.toDouble();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SectionHeader(
          title: 'Vue d\'ensemble',
          subtitle: '$modelName · $algo · ${points.length} jours prévus',
        ),
        LayoutBuilder(
          builder: (ctx, c) {
            final cardW = c.maxWidth < 640
                ? (c.maxWidth - 12) / 2
                : (c.maxWidth - 36) / 4;
            return Wrap(
              spacing: 12,
              runSpacing: 12,
              children: [
                SizedBox(
                  width: cardW,
                  child: KpiCard(
                    label: 'Production cumulée',
                    value: fmtBbl(total, compact: true),
                    icon: Icons.oil_barrel_rounded,
                    iconColor: AppColors.petrolDeep,
                  ),
                ),
                SizedBox(
                  width: cardW,
                  child: KpiCard(
                    label: 'Moyenne / jour',
                    value: fmtBblPerDay(avg),
                    icon: Icons.show_chart_rounded,
                    iconColor: AppColors.tealAccent,
                    delta: fmtDelta(trendPct),
                    deltaPositive: trendPct >= 0,
                  ),
                ),
                SizedBox(
                  width: cardW,
                  child: KpiCard(
                    label: 'Pic prévu',
                    value: fmtBbl(peak),
                    icon: Icons.trending_up_rounded,
                    iconColor: AppColors.goodGreen,
                  ),
                ),
                SizedBox(
                  width: cardW,
                  child: KpiCard(
                    label: 'Creux prévu',
                    value: fmtBbl(low),
                    icon: Icons.trending_down_rounded,
                    iconColor: AppColors.warnOrange,
                  ),
                ),
              ],
            );
          },
        ),
        const SizedBox(height: 20),
        SectionHeader(
          title: 'Courbe de prévision',
          subtitle: confidence == null
              ? null
              : 'Confiance modèle : ${(confidence * 100).toStringAsFixed(0)} %',
        ),
        Card(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(12, 20, 16, 8),
            child: SizedBox(
              height: 280,
              child: _ForecastChart(points: points),
            ),
          ),
        ),
        const SizedBox(height: 16),
        const SectionHeader(title: 'Détail jour par jour'),
        Card(
          child: _ForecastTable(points: points),
        ),
      ],
    );
  }
}

class _ForecastChart extends StatelessWidget {
  const _ForecastChart({required this.points});
  final List<Map<String, dynamic>> points;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final preds = <FlSpot>[];
    final upper = <FlSpot>[];
    final lower = <FlSpot>[];
    for (var i = 0; i < points.length; i++) {
      final p = points[i];
      preds.add(FlSpot(i.toDouble(),
          (p['predicted_oil_bbl'] as num?)?.toDouble() ?? 0));
      upper.add(FlSpot(i.toDouble(),
          (p['upper_bound_bbl'] as num?)?.toDouble() ?? 0));
      lower.add(FlSpot(i.toDouble(),
          (p['lower_bound_bbl'] as num?)?.toDouble() ?? 0));
    }

    final allValues = [...upper.map((p) => p.y), ...lower.map((p) => p.y)];
    final maxY = allValues.reduce((a, b) => a > b ? a : b);
    final minY = allValues.reduce((a, b) => a < b ? a : b);

    return LineChart(
      LineChartData(
        minY: (minY * 0.95).clamp(0, double.infinity),
        maxY: maxY * 1.05,
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
              reservedSize: 56,
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
              interval: (points.length / 6).ceilToDouble().clamp(1, 30),
              getTitlesWidget: (v, _) {
                final i = v.toInt();
                if (i < 0 || i >= points.length) return const SizedBox.shrink();
                final dateStr = points[i]['date']?.toString() ?? '';
                final short = dateStr.length >= 10
                    ? dateStr.substring(5)
                    : dateStr;
                return Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: Text(
                    short,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                );
              },
            ),
          ),
        ),
        lineTouchData: LineTouchData(
          touchTooltipData: LineTouchTooltipData(
            getTooltipColor: (_) =>
                scheme.surfaceContainerHigh.withValues(alpha: 0.95),
            getTooltipItems: (spots) => spots.map((s) {
              if (s.barIndex != 2) return null;
              final i = s.x.toInt();
              if (i < 0 || i >= points.length) return null;
              final p = points[i];
              return LineTooltipItem(
                '${p['date']}\n',
                TextStyle(
                  color: scheme.onSurface,
                  fontWeight: FontWeight.w700,
                ),
                children: [
                  TextSpan(
                    text:
                        '${fmtBbl(p['predicted_oil_bbl'] as num?)}\n[${fmtCompact(p['lower_bound_bbl'] as num?)} – ${fmtCompact(p['upper_bound_bbl'] as num?)}]',
                    style: TextStyle(
                      color: scheme.onSurface,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              );
            }).toList(),
          ),
        ),
        lineBarsData: [
          // Upper bound (invisible, just establishes shaded area)
          LineChartBarData(
            spots: upper,
            isCurved: true,
            color: Colors.transparent,
            barWidth: 0,
            dotData: const FlDotData(show: false),
            belowBarData: BarAreaData(
              show: true,
              color: scheme.primary.withValues(alpha: 0.18),
              cutOffY: 0,
              applyCutOffY: true,
            ),
          ),
          // Lower bound (cuts the area)
          LineChartBarData(
            spots: lower,
            isCurved: true,
            color: Colors.transparent,
            barWidth: 0,
            dotData: const FlDotData(show: false),
            belowBarData: BarAreaData(
              show: true,
              color: Theme.of(context).cardTheme.color ?? scheme.surface,
              cutOffY: 0,
              applyCutOffY: true,
            ),
          ),
          // Predicted line
          LineChartBarData(
            spots: preds,
            isCurved: true,
            barWidth: 3,
            dotData: const FlDotData(show: false),
            gradient: const LinearGradient(
              colors: [AppColors.petrolDeep, AppColors.tealAccent],
            ),
          ),
        ],
      ),
    );
  }
}

class _ForecastTable extends StatelessWidget {
  const _ForecastTable({required this.points});
  final List<Map<String, dynamic>> points;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return ClipRRect(
      borderRadius: BorderRadius.circular(AppRadii.lg),
      child: Column(
        children: [
          Container(
            color: scheme.surfaceContainerHighest.withValues(alpha: 0.5),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            child: Row(
              children: const [
                Expanded(
                  flex: 3,
                  child: Text('Date',
                      style: TextStyle(fontWeight: FontWeight.w700, fontSize: 12)),
                ),
                Expanded(
                  flex: 3,
                  child: Text('Prévue',
                      style: TextStyle(fontWeight: FontWeight.w700, fontSize: 12)),
                ),
                Expanded(
                  flex: 4,
                  child: Text('Intervalle 95 %',
                      style: TextStyle(fontWeight: FontWeight.w700, fontSize: 12),
                      textAlign: TextAlign.end),
                ),
              ],
            ),
          ),
          ListView.separated(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: points.length,
            separatorBuilder: (_, _) =>
                Divider(height: 1, color: scheme.outlineVariant.withValues(alpha: 0.4)),
            itemBuilder: (_, i) {
              final p = points[i];
              return Padding(
                padding:
                    const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                child: Row(
                  children: [
                    Expanded(
                      flex: 3,
                      child: Text(fmtDateShort(p['date'])),
                    ),
                    Expanded(
                      flex: 3,
                      child: Text(
                        fmtBbl(p['predicted_oil_bbl'] as num?),
                        style: const TextStyle(fontWeight: FontWeight.w700),
                      ),
                    ),
                    Expanded(
                      flex: 4,
                      child: Text(
                        '${fmtCompact(p['lower_bound_bbl'] as num?)} – ${fmtCompact(p['upper_bound_bbl'] as num?)}',
                        textAlign: TextAlign.end,
                        style: TextStyle(
                          color: scheme.onSurfaceVariant,
                          fontSize: 12.5,
                        ),
                      ),
                    ),
                  ],
                ),
              );
            },
          ),
        ],
      ),
    );
  }
}
