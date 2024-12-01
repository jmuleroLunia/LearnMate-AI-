import { ComponentFixture, TestBed } from '@angular/core/testing';

import { SubjectMockExamComponent } from './subject-mock-exam.component';

describe('SubjectMockExamComponent', () => {
  let component: SubjectMockExamComponent;
  let fixture: ComponentFixture<SubjectMockExamComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [SubjectMockExamComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(SubjectMockExamComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
