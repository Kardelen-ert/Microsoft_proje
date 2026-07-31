import 'package:flutter_test/flutter_test.dart';

import 'package:frontend/main.dart';

void main() {
  testWidgets('App renders diagnostic assistant title', (WidgetTester tester) async {
    await tester.pumpWidget(const MyApp());

    expect(find.text('Rayli Sistemler Asistani'), findsOneWidget);
    expect(find.text('RAG Destekli Teshis Sistemi'), findsOneWidget);
  });
}
