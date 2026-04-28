import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/formatters.dart';
import '../../../core/offline/cache_status.dart' show cacheStatusProvider, CacheStatus;
import '../../../core/providers.dart';
import '../../../core/theme.dart';
import '../../../core/widgets/error_state.dart';
import '../../../core/widgets/kpi_card.dart';
import '../../../core/widgets/loading_skeleton.dart';
import '../../../core/widgets/section_header.dart';
import '../data/dashboard_repository.dart';

const _kFeatureKey = 'dashboard.kpis';

final _repoProvider = Provider<DashboardRepository>(
  (ref) => DashboardRepository(ref.watch(apiClientProvider)),
);

final _kpisProvider = FutureProvider.family<Map<String, dynamic>, String>(
  (ref, period) async {
    final result = await ref.watch(_repoProvider).kpisCached(period: period);
    ref
        .read(cacheStatusProvider.notifier)
        .report(_kFeatureKey, CacheStatus.fromResult(result));
    return result.data;
  },
);

const _periods = {
  '7d': '7 jours',
  '30d': '30 jours',
  '90d': '90 jours',
  '1y': '1 an',
};

class DashboardScreen extends ConsumerStatefulWidget {
  const DashboardScreen({super.key});

  @override
  ConsumerState<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends ConsumerState<DashboardScreen> {
  String _period = '30d';

  @override
  Widget build(BuildContext context) {
    final kpis = ref.watch(_kpisProvider(_period));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Vue d\'ensemble'),
        actions: [
          IconButton(
            tooltip: 'Actualiser',
            icon: const Icon(Icons.refresh_rounded),
            onPressed: () => ref.invalidate(_kpisProvider(_period)),
          ),
          const SizedBox(width: 4),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () async => ref.invalidate(_kpisProvider(_period)),
        child: kpis.when(
          loading: () => const _DashboardLoading(),
          error: (e, _) => ErrorState(
            error: e,
            onRetry: () => ref.invalidate(_kpisProvider(_period)),
          ),
          data: (data) => _DashboardBody(
            data: data,
            period: _period,
            onPeriodChanged: (p) => setState(() => _period = p),
          ),
        ),
      ),
    );
  }
}

class _DashboardLoading extends StatelessWidget {
  const _DashboardLoading();

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: const [
        SizedBox(height: 8),
        Wrap(
          spacing: 12,
          runSpacing: 12,
          children: [KpiSkeleton(), KpiSkeleton(), KpiSkeleton(), KpiSkeleton()],
        ),
        SizedBox(height: 24),
        Skeleton(height: 240, radius: 16),
      ],
    );
  }
}

class _DashboardBody extends StatelessWidget {
  const _DashboardBody({
    required this.data,
    required this.period,
    required this.onPeriodChanged,
  });
  final Map<String, dynamic> data;
  final String period;
  final ValueChanged<String> onPeriodChanged;

  @override
  Widget build(BuildContext context) {
    final total = (data['production_total_bbl'] as num?)?.toDouble() ?? 0;
    final avg = (data['production_avg_bbl_day'] as num?)?.toDouble() ?? 0;
    final wc = (data['watercut_avg_pct'] as num?)?.toDouble() ?? 0;
    final wells = (data['active_wells_avg'] as num?)?.toDouble() ?? 0;
    final delta = data['delta_vs_previous_pct'] as num?;

    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        _PeriodSelector(value: period, onChanged: onPeriodChanged),
        const SizedBox(height: 16),
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
                    label: 'Production totale',
                    value: fmtBbl(total, compact: true),
                    icon: Icons.oil_barrel_rounded,
                    iconColor: AppColors.petrolDeep,
                    delta: delta != null ? fmtDelta(delta) : null,
                    deltaPositive: delta != null ? delta >= 0 : null,
                  ),
                ),
                SizedBox(
                  width: cardW,
                  child: KpiCard(
                    label: 'Moyenne / jour',
                    value: fmtBblPerDay(avg),
                    icon: Icons.show_chart_rounded,
                    iconColor: AppColors.tealAccent,
                  ),
                ),
                SizedBox(
                  width: cardW,
                  child: KpiCard(
                    label: 'Watercut moyen',
                    value: fmtPct(wc),
                    icon: Icons.water_drop_rounded,
                    iconColor: AppColors.warnOrange,
                  ),
                ),
                SizedBox(
                  width: cardW,
                  child: KpiCard(
                    label: 'Puits actifs (moy.)',
                    value: fmtNum(wells, decimals: 0),
                    icon: Icons.adjust_rounded,
                    iconColor: AppColors.goldAmber,
                  ),
                ),
              ],
            );
          },
        ),
        const SizedBox(height: 28),
        const SectionHeader(
          title: 'Synthèse',
          subtitle: 'Indicateurs comparés sur la période',
        ),
        Card(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(12, 20, 16, 8),
            child: SizedBox(
              height: 240,
              child: _SynthesisChart(
                total: total,
                avg: avg,
                watercut: wc,
                wells: wells,
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _PeriodSelector extends StatelessWidget {
  const _PeriodSelector({required this.value, required this.onChanged});
  final String value;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    return SegmentedButton<String>(
      segments: [
        for (final e in _periods.entries)
          ButtonSegment(value: e.key, label: Text(e.value)),
      ],
      selected: {value},
      onSelectionChanged: (s) => onChanged(s.first),
      showSelectedIcon: false,
      style: ButtonStyle(
        shape: WidgetStatePropertyAll(RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppRadii.md),
        )),
      ),
    );
  }
}

class _SynthesisChart extends StatelessWidget {
  const _SynthesisChart({
    required this.total,
    required this.avg,
    required this.watercut,
    required this.wells,
  });
  final double total;
  final double avg;
  final double watercut;
  final double wells;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final values = [
      ('Total /1k', total / 1000),
      ('Moy /100', avg / 100),
      ('WC %', watercut),
      ('Puits', wells),
    ];
    final maxY = values.map((e) => e.$2).fold<double>(1, (a, b) => a > b ? a : b);

    return BarChart(
      BarChartData(
        alignment: BarChartAlignment.spaceAround,
        maxY: maxY * 1.2,
        barGroups: [
          for (int i = 0; i < values.length; i++)
            BarChartGroupData(
              x: i,
              barRods: [
                BarChartRodData(
                  toY: values[i].$2,
                  width: 28,
                  borderRadius: BorderRadius.circular(6),
                  gradient: LinearGradient(
                    begin: Alignment.bottomCenter,
                    end: Alignment.topCenter,
                    colors: [
                      scheme.primary.withValues(alpha: 0.85),
                      AppColors.tealAccent.withValues(alpha: 0.85),
                    ],
                  ),
                ),
              ],
            ),
        ],
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
              reservedSize: 40,
              getTitlesWidget: (v, _) => Text(
                fmtCompact(v),
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ),
          ),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 30,
              getTitlesWidget: (v, _) {
                final i = v.toInt();
                if (i < 0 || i >= values.length) return const SizedBox.shrink();
                return Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: Text(
                    values[i].$1,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                );
              },
            ),
          ),
        ),
      ),
    );
  }
}
