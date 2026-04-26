import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers.dart';

class WaterScreen extends ConsumerStatefulWidget {
  const WaterScreen({super.key});

  @override
  ConsumerState<WaterScreen> createState() => _WaterScreenState();
}

class _WaterScreenState extends ConsumerState<WaterScreen> {
  final _blockCtrl = TextEditingController(text: 'X');
  final _targetCtrl = TextEditingController();
  Map<String, dynamic>? _result;
  bool _loading = false;
  String? _error;

  Future<void> _run() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final api = ref.read(apiClientProvider);
      final r = await api.dio.post('/v1/ml/predict/water', data: {
        'block': _blockCtrl.text,
        'target_oil_bbl': _targetCtrl.text.isEmpty
            ? null
            : double.tryParse(_targetCtrl.text),
      });
      setState(() => _result = Map<String, dynamic>.from(r.data as Map));
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Optimisation injection eau')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              controller: _blockCtrl,
              decoration: const InputDecoration(labelText: 'Bloc'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _targetCtrl,
              decoration: const InputDecoration(
                labelText: 'Production cible (bbl, optionnel)',
              ),
              keyboardType: TextInputType.number,
            ),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: _loading ? null : _run,
              child: _loading
                  ? const SizedBox(
                      width: 16, height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2))
                  : const Text('Calculer recommandation'),
            ),
            const SizedBox(height: 16),
            if (_error != null)
              Text(_error!, style: const TextStyle(color: Colors.red)),
            if (_result != null)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Text(_result.toString()),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
