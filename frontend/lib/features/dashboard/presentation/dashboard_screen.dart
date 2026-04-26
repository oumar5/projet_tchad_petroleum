import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../../core/providers.dart';
import '../data/dashboard_repository.dart';

final _repoProvider = Provider<DashboardRepository>(
  (ref) => DashboardRepository(ref.watch(apiClientProvider)),
);

final _kpisProvider = FutureProvider.family<Map<String, dynamic>, String>(
  (ref, period) => ref.watch(_repoProvider).kpis(period: period),
);

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
    final fmt = NumberFormat.decimalPattern('fr');

    return Scaffold(
      appBar: AppBar(
        title: const Text('Dashboard'),
        actions: [
          DropdownButton<String>(
            value: _period,
            items: ['7d', '30d', '90d', '1y']
                .map((p) => DropdownMenuItem(value: p, child: Text(p)))
                .toList(),
            onChanged: (v) => setState(() => _period = v ?? '30d'),
          ),
          const SizedBox(width: 12),
        ],
      ),
      body: kpis.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Erreur : $e')),
        data: (data) => _DashboardBody(data: data, fmt: fmt),
      ),
    );
  }
}

class _DashboardBody extends StatelessWidget {
  const _DashboardBody({required this.data, required this.fmt});
  final Map<String, dynamic> data;
  final NumberFormat fmt;

  @override
  Widget build(BuildContext context) {
    final total = (data['production_total_bbl'] as num).toDouble();
    final avg = (data['production_avg_bbl_day'] as num).toDouble();
    final wc = (data['watercut_avg_pct'] as num).toDouble();
    final wells = (data['active_wells_avg'] as num).toDouble();
    final delta = data['delta_vs_previous_pct'];

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Wrap(
          spacing: 12,
          runSpacing: 12,
          children: [
            _kpiCard('Production totale', '${fmt.format(total)} bbl'),
            _kpiCard('Moyenne jour', '${fmt.format(avg)} bbl/j'),
            _kpiCard('Watercut moyen', '${wc.toStringAsFixed(1)} %'),
            _kpiCard('Puits actifs', wells.toStringAsFixed(0)),
            if (delta != null)
              _kpiCard(
                'Δ vs période N-1',
                '${(delta as num).toStringAsFixed(1)} %',
              ),
          ],
        ),
        const SizedBox(height: 24),
        SizedBox(
          height: 240,
          child: BarChart(BarChartData(
            barGroups: [
              BarChartGroupData(x: 0, barRods: [BarChartRodData(toY: total / 1000)]),
              BarChartGroupData(x: 1, barRods: [BarChartRodData(toY: avg / 100)]),
              BarChartGroupData(x: 2, barRods: [BarChartRodData(toY: wc)]),
              BarChartGroupData(x: 3, barRods: [BarChartRodData(toY: wells)]),
            ],
            titlesData: FlTitlesData(
              bottomTitles: AxisTitles(
                sideTitles: SideTitles(
                  showTitles: true,
                  getTitlesWidget: (v, _) {
                    const labels = ['Total/k', 'Avg/100', 'WC%', 'Puits'];
                    final i = v.toInt();
                    return Text(i >= 0 && i < labels.length ? labels[i] : '');
                  },
                ),
              ),
              leftTitles: const AxisTitles(
                sideTitles: SideTitles(showTitles: true, reservedSize: 40),
              ),
              rightTitles: const AxisTitles(),
              topTitles: const AxisTitles(),
            ),
          )),
        ),
      ],
    );
  }

  Widget _kpiCard(String label, String value) => Container(
        width: 200,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          boxShadow: const [
            BoxShadow(blurRadius: 4, color: Color(0x14000000)),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label, style: const TextStyle(color: Colors.black54)),
            const SizedBox(height: 8),
            Text(value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w600)),
          ],
        ),
      );
}
