from datetime import datetime, timezone
from sqlalchemy.orm import joinedload
from database import SessionLocal
from models import User, UserHistory, QA, PDFBlock, PDFDocument


def user_history_menu(user):
    """Menu principal do histórico do usuário"""
    while True:
        print("\n1. Visualizar QAs")
        print("2. Visualizar Desempenho por QA")
        print("3. Voltar ao Menu Principal")
        
        escolha = input("\nEscolha uma opção: ").strip()
        
        if escolha == "1":
            visualizar_qas(user)
        elif escolha == "2":
            visualizar_desempenho_por_qa(user)
        elif escolha == "3":
            break
        else:
            print("❌ Opção inválida! Tente novamente.")


def visualizar_qas(user):
    """Visualiza todos os Q&As do usuário com informações do PDF e bloco"""
    db = SessionLocal()
    try:
        # Busca todos os Q&As do usuário com joins para obter informações completas
        qas = db.query(QA).join(PDFBlock).join(PDFDocument).filter(
            QA.user_id == user.id
        ).options(
            joinedload(QA.pdf_block).joinedload(PDFBlock.pdf_document)
        ).all()
        
        if not qas:
            print("\n📝 Você ainda não possui Q&As criados.")
            return
        
        print(f"\n=== SEUS QAs ({len(qas)} encontrados) ===\n")
        
        for i, qa in enumerate(qas, 1):
            pdf_path = qa.pdf_block.pdf_document.file_path
            pdf_name = pdf_path.split('/')[-1] if '/' in pdf_path else pdf_path
            # Remove quebra de linha para visualização
            qa.pdf_block.text_content = qa.pdf_block.text_content.replace('\n', ' ')

            # Formatação inteligente do bloco
            bloco_texto = qa.pdf_block.text_content
            if len(bloco_texto) > 100:
                bloco_display = f"{bloco_texto[:50]}...{bloco_texto[-50:]}"
            else:
                bloco_display = bloco_texto[:50]
            
            if len(qa.question) > 50:
                pergunta_display = f"{qa.question[:50]}..."
            else:
                pergunta_display = qa.question
            
            if len(qa.answer) > 50:
                resposta_display = f"{qa.answer[:50]}..."
            else:
                resposta_display = qa.answer

            print(f"┌─ Q&A #{i} ─────────────────────────────────────────────")
            print(f"│ 📄 PDF: {pdf_name}")
            print(f"│ 📍 Caminho: {pdf_path}")
            print(f"│ 📦 Bloco: {bloco_display}")
            print(f"│")
            print(f"│ ❓ PERGUNTA:")
            print(f"│    {pergunta_display}")
            print(f"│")
            print(f"│ ✅ RESPOSTA:")
            print(f"│    {resposta_display}")
            print(f"└─────────────────────────────────────────────────────")
            
            if i < len(qas):
                print()
        
        input("\nPressione ENTER para continuar...")
        
    except Exception as e:
        print(f"❌ Erro ao buscar Q&As: {e}")
    finally:
        db.close()


def visualizar_desempenho_por_qa(user):
    """Visualiza o desempenho do usuário para cada Q&A"""
    db = SessionLocal()
    try:
        # Busca o histórico do usuário com informações dos Q&As
        historico = db.query(UserHistory).join(QA).filter(
            QA.user_id == user.id
        ).options(joinedload(UserHistory.qa)).all()
        
        if not historico:
            print("\n📊 Você ainda não possui histórico de estudos.")
            return
        
        # Agrupa por Q&A
        qa_performance = {}
        for entry in historico:
            qa_id = entry.qa_id
            if qa_id not in qa_performance:
                qa_performance[qa_id] = {
                    'qa': entry.qa,
                    'tentativas': [],
                    'notas': [],
                    'ultima_revisao': None,
                    'proxima_revisao': None
                }
            
            qa_performance[qa_id]['tentativas'].append(entry)
            if entry.grade is not None:
                qa_performance[qa_id]['notas'].append(entry.grade)
            if entry.review:
                qa_performance[qa_id]['ultima_revisao'] = entry.review
            if entry.due:
                qa_performance[qa_id]['proxima_revisao'] = entry.due
        
        print(f"\n=== DESEMPENHO POR QA ({len(qa_performance)} Q&As) ===\n")
        
        for i, (qa_id, data) in enumerate(qa_performance.items(), 1):
            qa = data['qa']
            tentativas = len(data['tentativas'])
            notas = data['notas']
            
            # Cálculos de desempenho
            media_nota = sum(notas) / len(notas) if notas else 0
            melhor_nota = max(notas) if notas else 0
            pior_nota = min(notas) if notas else 0
            ultima_nota = notas[-1] if notas else 0
            
            # Status baseado na última nota
            if ultima_nota >= 4:
                status = "🟢 Excelente"
            elif ultima_nota >= 3:
                status = "🟡 Bom"
            elif ultima_nota >= 2:
                status = "🟠 Regular"
            else:
                status = "🔴 Precisa Revisar"
            
            if len(qa.question) > 50:
                pergunta_display = f"{qa.question[:50]}..."
            else:
                pergunta_display = qa.question
            
            if len(qa.answer) > 50:
                resposta_display = f"{qa.answer[:50]}..."
            else:
                resposta_display = qa.answer

            print(f"┌─ Q&A #{i} ─────────────────────────────────────────────")
            print(f"│ ❓ PERGUNTA:")
            print(f"│    {pergunta_display}")
            print(f"│")
            print(f"│ ✅ RESPOSTA CORRETA:")
            print(f"│    {resposta_display}")
            print(f"│")
            print(f"│ 📊 RESUMO DE DESEMPENHO:")
            print(f"│    Status: {status}")
            print(f"│    Tentativas: {tentativas}")
            print(f"│    Média de Notas: {media_nota:.1f}")
            print(f"│    Melhor Nota: {melhor_nota}")
            print(f"│    Pior Nota: {pior_nota}")
            print(f"│    Última Nota: {ultima_nota}")
            
            if data['ultima_revisao']:
                # Converte de UTC para timezone local para exibição
                ultima_revisao_local = data['ultima_revisao'].replace(tzinfo=timezone.utc).astimezone()
                print(f"│    Última Revisão: {ultima_revisao_local.strftime('%d/%m/%Y %H:%M')}")
            
            if data['proxima_revisao']:
                # Usa UTC para cálculos de diferença de tempo
                now_utc = datetime.now(timezone.utc)
                proxima_revisao_utc = data['proxima_revisao'].replace(tzinfo=timezone.utc)
                # Converte para timezone local para exibição
                proxima_revisao_local = proxima_revisao_utc.astimezone()
                print(f"│    Próxima Revisão: {proxima_revisao_local.strftime('%d/%m/%Y %H:%M')}")
            
            print(f"└─────────────────────────────────────────────────────")
            
            if i < len(qa_performance):
                print()
        
        # Estatísticas gerais
        total_tentativas = sum(len(data['tentativas']) for data in qa_performance.values())
        todas_notas = []
        for data in qa_performance.values():
            todas_notas.extend(data['notas'])
        
        if todas_notas:
            media_geral = sum(todas_notas) / len(todas_notas)
            print(f"\n📈 ESTATÍSTICAS GERAIS:")
            print(f"   Total de QAs: {len(qa_performance)}")
            print(f"   Total de Tentativas: {total_tentativas}")
            print(f"   Média Geral: {media_geral:.1f}")
            print(f"   Total de Avaliações: {len(todas_notas)}")
        
        input("\nPressione ENTER para continuar...")
        
    except Exception as e:
        print(f"❌ Erro ao buscar desempenho: {e}")
    finally:
        db.close()


def obter_estatisticas_usuario(user):
    """Função auxiliar para obter estatísticas gerais do usuário"""
    db = SessionLocal()
    try:
        # Total de Q&As criados
        total_qas = db.query(QA).filter(QA.user_id == user.id).count()
        
        # Total de estudos realizados
        total_estudos = db.query(UserHistory).join(QA).filter(
            QA.user_id == user.id
        ).count()
        
        # Média geral de notas
        notas = db.query(UserHistory.grade).join(QA).filter(
            QA.user_id == user.id,
            UserHistory.grade.isnot(None)
        ).all()
        
        media_geral = sum(nota[0] for nota in notas) / len(notas) if notas else 0
        
        return {
            'total_qas': total_qas,
            'total_estudos': total_estudos,
            'media_geral': media_geral,
            'total_avaliacoes': len(notas)
        }
    
    except Exception as e:
        print(f"❌ Erro ao obter estatísticas: {e}")
        return None
    finally:
        db.close()
