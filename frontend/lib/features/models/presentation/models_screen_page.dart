import 'package:flutter/material.dart';

import 'models_screen.dart';

/// Top-level "Modèles IA" entry point used by the sidebar.
/// Wraps [ModelsManagementView] in a [Scaffold] + [AppBar].
class ModelsScreenPage extends StatelessWidget {
  const ModelsScreenPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Modèles IA'),
      ),
      body: const ModelsManagementView(),
    );
  }
}
