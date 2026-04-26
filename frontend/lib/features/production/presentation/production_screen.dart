import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';
import '../data/production_repository.dart';

final _repoProvider = Provider<ProductionRepository>(
  (ref) => ProductionRepository(ref.watch(apiClientProvider)),
);

final _dailyProvider = FutureProvider<List<Map<String, dynamic>>>(
  (ref) => ref.watch(_repoProvider).daily(),
);

class ProductionScreen extends ConsumerWidget {
  const ProductionScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final daily = ref.watch(_dailyProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Production'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.invalidate(_dailyProvider),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showCreateDialog(context, ref),
        child: const Icon(Icons.add),
      ),
      body: daily.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Erreur : $e')),
        data: (items) => ListView.separated(
          itemCount: items.length,
          separatorBuilder: (_, _) => const Divider(height: 1),
          itemBuilder: (_, i) {
            final r = items[i];
            return ListTile(
              title: Text('${r['date']} — Bloc ${r['block']}'),
              subtitle: Text(
                'Huile : ${r['oil_bbl']} bbl · Watercut : ${r['watercut_pct']}%',
              ),
              trailing: Text('Puits ${r['wells_active']}/${r['wells_total']}'),
            );
          },
        ),
      ),
    );
  }

  void _showCreateDialog(BuildContext context, WidgetRef ref) {
    final dateCtrl = TextEditingController(
        text: DateTime.now().toIso8601String().substring(0, 10));
    final blockCtrl = TextEditingController(text: 'X');
    final oilCtrl = TextEditingController();
    final waterCtrl = TextEditingController();
    final wcCtrl = TextEditingController();
    final wtCtrl = TextEditingController(text: '20');
    final waCtrl = TextEditingController(text: '18');

    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Nouvelle ligne'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(controller: dateCtrl, decoration: const InputDecoration(labelText: 'Date YYYY-MM-DD')),
              TextField(controller: blockCtrl, decoration: const InputDecoration(labelText: 'Bloc')),
              TextField(controller: wtCtrl, decoration: const InputDecoration(labelText: 'Puits totaux'), keyboardType: TextInputType.number),
              TextField(controller: waCtrl, decoration: const InputDecoration(labelText: 'Puits actifs'), keyboardType: TextInputType.number),
              TextField(controller: oilCtrl, decoration: const InputDecoration(labelText: 'Huile (bbl)'), keyboardType: TextInputType.number),
              TextField(controller: waterCtrl, decoration: const InputDecoration(labelText: 'Eau (bbl)'), keyboardType: TextInputType.number),
              TextField(controller: wcCtrl, decoration: const InputDecoration(labelText: 'Watercut %'), keyboardType: TextInputType.number),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Annuler')),
          FilledButton(
            onPressed: () async {
              try {
                await ref.read(_repoProvider).create(
                      date: dateCtrl.text,
                      blockCode: blockCtrl.text,
                      wellsTotal: int.parse(wtCtrl.text),
                      wellsActive: int.parse(waCtrl.text),
                      oilBbl: double.parse(oilCtrl.text),
                      waterBbl: double.parse(waterCtrl.text),
                      watercutPct: double.parse(wcCtrl.text),
                    );
                if (context.mounted) Navigator.pop(context);
                ref.invalidate(_dailyProvider);
              } catch (e) {
                if (context.mounted) {
                  ScaffoldMessenger.of(context)
                      .showSnackBar(SnackBar(content: Text('Erreur : $e')));
                }
              }
            },
            child: const Text('Créer'),
          ),
        ],
      ),
    );
  }
}
