import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px

def init_db():
    conn = sqlite3.connect('daily_planner.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tasks
                 (id INTEGER PRIMARY KEY,
                  date TEXT,
                  scheduled_time TEXT,
                  description TEXT,
                  priority TEXT,
                  status TEXT,
                  category TEXT)''')
    conn.commit()
    conn.close()

def add_task(date, scheduled_time, description, priority, category, status="Pendente"):
    conn = sqlite3.connect('daily_planner.db')
    c = conn.cursor()
    c.execute('''INSERT INTO tasks (date, scheduled_time, description, priority, status, category)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (date, scheduled_time, description, priority, status, category))
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = sqlite3.connect('daily_planner.db')
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def get_weekly_stats():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    conn = sqlite3.connect('daily_planner.db')
    query = """
    SELECT date, status, COUNT(*) as count 
    FROM tasks 
    WHERE date BETWEEN ? AND ?
    GROUP BY date, status
    """
    df = pd.read_sql_query(query, conn, params=(start_date.strftime("%Y-%m-%d"), 
                                               end_date.strftime("%Y-%m-%d")))
    conn.close()
    return df

def get_tasks(date=None):
    conn = sqlite3.connect('daily_planner.db')
    if date:
        query = "SELECT * FROM tasks WHERE date = ? ORDER BY scheduled_time"
        df = pd.read_sql_query(query, conn, params=(date,))
    else:
        df = pd.read_sql_query("SELECT * FROM tasks ORDER BY date, scheduled_time", conn)
    conn.close()
    return df

def main():
    st.title("Planejamento Diário")
    init_db()

    st.sidebar.header("Menu")
    page = st.sidebar.selectbox("Escolha uma opção", 
                              ["Adicionar Tarefa", "Visualizar Tarefas", "Dashboard", "Resumo Semanal"])

    if page == "Adicionar Tarefa":
        st.subheader("Nova Tarefa")
        
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("Data", datetime.now())
        with col2:
            scheduled_time = st.time_input("Horário Planejado", datetime.now().time())
            
        description = st.text_area("Descrição da Tarefa")
        priority = st.selectbox("Prioridade", ["Alta", "Média", "Baixa"])
        category = st.selectbox("Categoria", ["Trabalho", "Pessoal", "Estudo", "Saúde"])
        
        if st.button("Adicionar"):
            add_task(
                date.strftime("%Y-%m-%d"),
                scheduled_time.strftime("%H:%M"),
                description,
                priority,
                category
            )
            st.success("Tarefa adicionada com sucesso!")

    elif page == "Dashboard":
        st.subheader("Dashboard de Tarefas")
        
        all_tasks = get_tasks()
        if not all_tasks.empty:
            status_counts = all_tasks['status'].value_counts()
            fig = px.pie(values=status_counts.values, 
                        names=status_counts.index, 
                        title='Distribuição de Status das Tarefas')
            st.plotly_chart(fig)
            
            category_status = pd.crosstab(all_tasks['category'], all_tasks['status'])
            fig2 = px.bar(category_status, 
                         title='Status por Categoria',
                         barmode='group')
            st.plotly_chart(fig2)
        else:
            st.warning("Sem tarefas registradas no sistema")

    elif page == "Resumo Semanal":
        st.subheader("Resumo Semanal")
        
        weekly_stats = get_weekly_stats()
        if not weekly_stats.empty:
            fig = px.line(weekly_stats, 
                         x='date', 
                         y='count', 
                         color='status',
                         title='Progresso Semanal')
            st.plotly_chart(fig)
            
            st.metric("Total de Tarefas Concluídas", 
                     len(weekly_stats[weekly_stats['status'] == 'Concluída']))
        else:
            st.warning("Sem tarefas registradas para a última semana")

    else:  # Visualizar Tarefas
        st.subheader("Minhas Tarefas")
        
        filter_date = st.date_input("Filtrar por data", datetime.now())
        tasks = get_tasks(filter_date.strftime("%Y-%m-%d"))
        
        if not tasks.empty:
            for idx, task in tasks.iterrows():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"**{task['scheduled_time']} - {task['description']}**")
                    st.write(f"Prioridade: {task['priority']} | Categoria: {task['category']}")
                
                with col2:
                    status = st.selectbox(
                        "Status",
                        ["Pendente", "Em Andamento", "Concluída"],
                        index=["Pendente", "Em Andamento", "Concluída"].index(task['status']),
                        key=f"status_{task['id']}"
                    )
                
                with col3:
                    if task['status'] != "Pendente":
                        if st.button("Excluir", key=f"del_{task['id']}"):
                            delete_task(task['id'])
                            st.experimental_rerun()
                
                st.divider()
        else:
            st.warning("Sem tarefas para o período")

if __name__ == "__main__":
    main()
